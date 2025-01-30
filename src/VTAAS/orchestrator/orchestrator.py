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


class Orchestrator:
    """Orchestrator class to manage actors and assertors."""

    def __init__(self, browser: Browser | None = None):
        self.workers: list[Worker] = []
        self.active_workers: list[Worker] = []
        self.llm_client: LLMClient = LLMClient()
        self._browser: Browser | None = browser
        self._test_case: TestCase | None = None
        self._current_step: tuple[str, str] | None = None
        self.worker_reports: dict[str, list[str]] = {}
        self.worker_counter: dict[str, int] = {"actor": 0, "assertor": 0}
        self.conversation: list[Message] = []
        logger.info("Orchestrator initialized")

    def get_verdict_prompt(self, result: list[WorkerResult], assertion: str) -> str:
        return f"action: {result}, assertion: {assertion}"

    @property
    def test_case(self) -> TestCase:
        """Get the test_case instance, ensuring it is initialized"""
        if self._test_case is None:
            raise RuntimeError(
                "No test case is being processed. Call process_TestCase()."
            )
        return self._test_case

    @property
    def current_step(self) -> tuple[str, str]:
        """Get the current test step, ensuring it is initialized"""
        if self._current_step is None:
            raise RuntimeError(
                "No test case is being processed. Call process_TestCase()."
            )
        return self._current_step

    async def process_testcase(self, test_case: TestCase) -> TestCaseVerdict:
        """Manages the main execution loop for the given Test Case."""

        logger.info(f"Processing {test_case.name}")
        self._test_case = test_case
        if self._browser is None:
            self._browser = await Browser.create(timeout=3500, headless=True)
        _ = await self.browser.goto(self.test_case.url)
        results: list[WorkerResult] = []
        for idx, _ in enumerate(test_case):
            verdict = await self.process_step(idx)
            if verdict.status == Status.FAIL:
                break

        if all(verdict.status == Status.PASS for verdict in results):
            return TestCaseVerdict(status=Status.PASS, explaination=None)
        else:
            return TestCaseVerdict(status=Status.FAIL, explaination=None)

    async def process_step(self, step_index: int) -> BaseResult:
        self._current_step = self.test_case.get_step(step_index)
        screenshot = await self.browser.screenshot()
        self._setup_conversation(step_index, screenshot)
        results: list[WorkerResult] = []
        sequence_type = await self.plan_step_init()
        for i in range(4):
            logger.info(f"step #{step_index}: processing iteration {i}")
            results = await self.execute_step()
            success = not any(verdict.status != Status.PASS for verdict in results)
            if sequence_type == SequenceType.full and success:
                return BaseResult(status=Status.PASS)
            self.conversation.append(self.merge_worker_results(success, results))
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

    def merge_worker_results(self, success: bool, results: list[WorkerResult]):
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

    async def execute_step(self) -> list[WorkerResult]:
        """
        Process active workers and retire them after processing.
        """
        results: list[WorkerResult] = []
        result = BaseResult(status=Status.PASS)
        while self.active_workers and result.status == Status.PASS:
            worker = self.active_workers[0]
            input: WorkerInput = self._prepare_worker_input(worker.type)
            result = await worker.process(input=input)
            results.append(result)
            worker.status = WorkerStatus.RETIRED
            self.active_workers.remove(worker)
        return results

    def _prepare_worker_input(self, type: WorkerType) -> WorkerInput:
        match type:
            case WorkerType.ACTOR:
                return ActorInput(
                    test_case=self.test_case.__str__(),
                    test_step=self.current_step,
                    history=None,
                )
            case WorkerType.ASSERTOR:
                return AssertorInput(
                    test_case=self.test_case.__str__(),
                    test_step=self.current_step,
                    history=None,
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
        self, test_step_index: int, screenshot: bytes, history: str | None = None
    ):
        self.conversation = [
            Message(role=MessageRole.System, content=self._build_system_prompt()),
            Message(
                role=MessageRole.User,
                content=self._build_user_plan_prompt(test_step_index, history),
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

    def _build_user_plan_prompt(
        self, test_step_index: int, history: str | None = None
    ) -> str:
        with open(
            "./src/VTAAS/orchestrator/init_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()
        test_case = self.test_case
        action, assertion = self.current_step
        test_step = f"{test_step_index}. action: {action}, assertion: {assertion}"
        return prompt_template.format(
            test_case=test_case, current_step=test_step, history=history
        )

    def _build_user_followup_message(
        self, previous_results: list[WorkerResult]
    ) -> Message:
        role = MessageRole.User
        content = self._build_user_followup_prompt(previous_results)
        screenshots = [r.screenshot for r in previous_results]
        return Message(role=role, content=content, screenshot=screenshots)

    def _build_user_followup_prompt(self, previous_results: list[WorkerResult]) -> str:
        with open(
            "./src/VTAAS/orchestrator/followup_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()
        formatted_results = ""
        for result in previous_results:
            if isinstance(result, ActorResult):
                actions_str = "\n".join(
                    [f"  - {action.chain_of_thought}" for action in result.actions]
                )
                formatted_results += (
                    f'Act("{result.query}") -> {result.status.value}\n'
                    f"  Actions:\n{actions_str}\n"
                    "-----------------\n"
                )
            else:
                formatted_results += (
                    f'Assert("{result.query}") -> {result.status.value}\n'
                    f"  Report: {result.synthesis}\n"
                    "-----------------\n"
                )
        return prompt_template.format(worker_results=formatted_results)

    @property
    def browser(self) -> Browser:
        """Get the browser instance, ensuring it is initialized"""
        if self._browser is None:
            raise RuntimeError(
                "Browser has not been initialized yet. Do Browser.create(name)."
            )
        return self._browser
