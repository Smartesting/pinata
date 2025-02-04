from dataclasses import dataclass, field
from VTAAS.schemas.llm import SequenceType
from ..data.testcase import TestCase
from ..schemas.verdict import (
    ActorResult,
    BaseResult,
    TestCaseVerdict,
    Status,
    WorkerResult,
)
from ..workers.browser import Browser
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..workers.actor import Actor
from ..workers.assertor import Assertor
from ..schemas.worker import (
    ActorInput,
    AssertorInput,
    Message,
    MessageRole,
    Worker,
    WorkerConfig,
    WorkerInput,
    WorkerStatus,
    WorkerType,
)

logger = get_logger(__name__)


@dataclass
class TestExecutionContext:
    test_case: TestCase
    current_step: tuple[str, str]
    step_index: int
    history: list[str] = field(default_factory=list)


class Orchestrator:
    """Orchestrator class to manage actors and assertors."""

    def __init__(self, browser: Browser | None = None):
        self.workers: list[Worker] = []
        self.active_workers: list[Worker] = []
        self.llm_client: LLMClient = LLMClient()
        self._browser: Browser | None = browser
        self._exec_context: TestExecutionContext | None = None
        self._followup_prompt: str | None = None
        self._recover_prompt: str | None = None
        self.worker_reports: dict[str, list[str]] = {}
        self.worker_counter: dict[str, int] = {"actor": 0, "assertor": 0}
        self.conversation: list[Message] = []
        logger.info("Orchestrator initialized")

    async def process_testcase(self, test_case: TestCase) -> TestCaseVerdict:
        """Manages the main execution loop for the given Test Case."""

        logger.info(f"Processing {test_case.name}")
        exec_context = TestExecutionContext(
            test_case=test_case, current_step=test_case.get_step(1), step_index=1
        )
        if self._browser is None:
            self._browser = await Browser.create(timeout=3500, headless=True)
        _ = await self.browser.goto(exec_context.test_case.url)
        done_steps: list[str] = []
        verdict = BaseResult(status=Status.UNK)
        for idx, test_step in enumerate(test_case):
            exec_context.current_step = test_step
            exec_context.step_index = idx + 1
            verdict = await self.process_step(exec_context)
            if verdict.status != Status.PASS:
                break
            step_str = f"{exec_context.step_index}. {test_step[0]} -> {test_step[1]}"
            done_steps.append(step_str)
            exec_context.history = done_steps.copy()

        if verdict.status == Status.PASS:
            return TestCaseVerdict(status=Status.PASS, explaination=None)
        else:
            return TestCaseVerdict(status=Status.FAIL, explaination=None)

    async def process_step(self, exec_context: TestExecutionContext) -> BaseResult:
        screenshot = await self.browser.screenshot()
        self._setup_conversation(exec_context, screenshot)
        results: list[WorkerResult] = []
        sequence_type = await self.plan_step_init()
        for i in range(4):
            logger.info(f"step #{exec_context.step_index}: processing iteration {i}")
            results = await self.execute_step(exec_context)
            success = not any(verdict.status != Status.PASS for verdict in results)
            if sequence_type == SequenceType.full and success:
                return BaseResult(status=Status.PASS)
            self.conversation.append(self._merge_worker_results(success, results))
            if success:
                sequence_type = await self.plan_step_followup()
            else:
                recovery = await self.plan_step_recover()
                if not recovery:
                    return BaseResult(status=Status.FAIL)
                else:
                    sequence_type = recovery
        return BaseResult(status=Status.FAIL)

    async def plan_step_init(self) -> SequenceType:
        """Planning for the test step: spawn workers based on LLM call."""
        response = await self.llm_client.plan_step(self.conversation)
        self.conversation.append(
            Message(
                role=MessageRole.Assistant,
                content=response.model_dump_json(),
            )
        )
        for config in response.workers:
            _ = self.spawn_worker(config)
        logger.info(f"Initialized {len(self.active_workers)} new workers")
        return response.sequence_type

    async def plan_step_followup(self) -> SequenceType:
        """Continuing planning for the test step: spawn workers based on LLM call."""
        response = await self.llm_client.followup_step(self.conversation)
        self.conversation.append(
            Message(
                role=MessageRole.Assistant,
                content=response.model_dump_json(),
            )
        )
        for config in response.workers:
            _ = self.spawn_worker(config)
        logger.info(f"Initialized {len(self.active_workers)} new workers")
        return response.sequence_type

    async def plan_step_recover(self) -> SequenceType | bool:
        """Recover planning of the test step: spawn workers based on LLM call."""
        response = await self.llm_client.recover_step(self.conversation)
        self.conversation.append(
            Message(
                role=MessageRole.Assistant,
                content=response.model_dump_json(),
            )
        )
        if not response.plan:
            return False
        for config in response.plan.workers:
            _ = self.spawn_worker(config)
        logger.info(f"Initialized {len(self.active_workers)} new workers")
        return response.plan.sequence_type

    async def execute_step(
        self, exec_context: TestExecutionContext
    ) -> list[WorkerResult]:
        """
        Run active workers and retire them afterwards.
        """
        results: list[WorkerResult] = []
        result = BaseResult(status=Status.PASS)
        while self.active_workers and result.status == Status.PASS:
            worker = self.active_workers[0]
            input: WorkerInput = self._prepare_worker_input(exec_context, worker.type)
            result = await worker.process(input=input)
            self._save_worker_result(exec_context, result)
            results.append(result)
            worker.status = WorkerStatus.RETIRED
            self.active_workers.remove(worker)
        self.active_workers.clear()
        return results

    def _save_worker_result(
        self, exec_context: TestExecutionContext, result: WorkerResult
    ):
        if isinstance(result, ActorResult):
            for action in result.actions:
                if action:
                    exec_context.history.append(action.action)
        else:
            exec_context.history.append(f'Verified: "{result.query}"')

    def _merge_worker_results(self, success: bool, results: list[WorkerResult]):
        outcome: str = "successfully" if success else "but eventually failed"
        user_msg: str = f"The sequence of workers was executed {outcome}:"
        screenshots: list[bytes] = []
        for result in results:
            screenshots.append(result.screenshot)
            if isinstance(result, ActorResult):
                actions_str = "\n".join(
                    [f"  - {action.chain_of_thought}" for action in result.actions]
                )
                user_msg += (
                    f'Act("{result.query}") -> {result.status.value}\n'
                    f"  Actions:\n{actions_str}\n"
                    "-----------------\n"
                )
            else:
                user_msg += (
                    f'Assert("{result.query}") -> {result.status.value}\n'
                    f"  Report: {result.synthesis}\n"
                    "-----------------\n"
                )
        if success:
            with open(
                "./src/VTAAS/orchestrator/followup_prompt.txt", "r", encoding="utf-8"
            ) as prompt_file:
                user_msg += prompt_file.read()

        else:
            with open(
                "./src/VTAAS/orchestrator/recover_prompt.txt", "r", encoding="utf-8"
            ) as prompt_file:
                user_msg += prompt_file.read()

        return Message(role=MessageRole.User, content=user_msg, screenshot=screenshots)

    def _prepare_worker_input(
        self, exec_context: TestExecutionContext, type: WorkerType
    ) -> WorkerInput:
        match type:
            case WorkerType.ACTOR:
                return ActorInput(
                    test_case=exec_context.test_case.__str__(),
                    test_step=exec_context.current_step,
                    history=("\n").join(exec_context.history),
                )
            case WorkerType.ASSERTOR:
                return AssertorInput(
                    test_case=exec_context.test_case.__str__(),
                    test_step=exec_context.current_step,
                    history=("\n").join(exec_context.history),
                )

    def spawn_worker(self, config: WorkerConfig) -> Worker:
        """Spawn a new worker based on the provided configuration."""
        worker: Worker
        match config.type:
            case WorkerType.ACTOR:
                worker = Actor(config.query, self.browser)
                self.workers.append(worker)
                self.active_workers.append(worker)
            case WorkerType.ASSERTOR:
                worker = Assertor(config.query, self.browser)
                self.workers.append(worker)
                self.active_workers.append(worker)
        return worker

    def _setup_conversation(
        self,
        context: TestExecutionContext,
        screenshot: bytes,
        history: str | None = None,
    ):
        self.conversation = [
            Message(role=MessageRole.System, content=self._build_system_prompt()),
            Message(
                role=MessageRole.User,
                content=self._build_user_init_prompt(context, history),
                screenshot=[screenshot],
            ),
        ]
        logger.debug(f"User prompt:\n{self.conversation[1].content}")

    def _build_system_prompt(self) -> str:
        with open(
            "./src/VTAAS/orchestrator/system_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()
        return prompt_template

    def _build_user_init_prompt(
        self, exec_context: TestExecutionContext, history: str | None = None
    ) -> str:
        with open(
            "./src/VTAAS/orchestrator/init_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()
        test_case = exec_context.test_case
        action, assertion = exec_context.current_step
        test_step = (
            f"{exec_context.step_index}. action: {action}, assertion: {assertion}"
        )
        return prompt_template.format(
            test_case=test_case, current_step=test_step, history=history
        )

    @property
    def browser(self) -> Browser:
        """Get the browser instance, ensuring it is initialized"""
        if self._browser is None:
            raise RuntimeError(
                "Browser has not been initialized yet. Do Browser.create(name)."
            )
        return self._browser

    @property
    def followup_prompt(self) -> str:
        """Get the followup prompt"""
        if self._followup_prompt is None:
            with open(
                "./src/VTAAS/orchestrator/followup_prompt.txt", "r", encoding="utf-8"
            ) as prompt_file:
                self._followup_prompt = prompt_file.read()
        return self._followup_prompt

    @property
    def recover_prompt(self) -> str:
        """Get the recover prompt"""
        if self._recover_prompt is None:
            with open(
                "./src/VTAAS/orchestrator/recover_prompt.txt", "r", encoding="utf-8"
            ) as prompt_file:
                self._recover_prompt = prompt_file.read()
        return self._recover_prompt
