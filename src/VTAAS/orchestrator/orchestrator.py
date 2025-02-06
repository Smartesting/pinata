from dataclasses import dataclass, field
from VTAAS.schemas.llm import SynthesisEntry, SequenceType
from ..data.testcase import TestCase
from ..schemas.verdict import (
    ActorResult,
    BaseResult,
    TestCaseVerdict,
    Status,
    TestStepVerdict,
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
    synthesis: list[str] = field(default_factory=list)


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
        verdict = BaseResult(status=Status.UNK)
        for idx, test_step in enumerate(test_case):
            exec_context.current_step = test_step
            exec_context.step_index = idx + 1
            verdict = await self.process_step(exec_context)
            if verdict.status != Status.PASS:
                return TestCaseVerdict(
                    status=Status.FAIL, step_index=idx, explaination=None
                )
            step_str = (
                f"\n\n{exec_context.step_index}. {test_step[0]} -> {test_step[1]}\n"
            )
            step_synthesis = await self.step_synthesis(
                exec_context, verdict.history, exec_context.synthesis
            )
            exec_context.synthesis.append(step_str)
            exec_context.synthesis.append(self.synthesis_str(step_synthesis))

        return TestCaseVerdict(status=Status.PASS, explaination=None)

    async def process_step(self, exec_context: TestExecutionContext) -> TestStepVerdict:
        screenshot = await self.browser.screenshot()
        results: list[WorkerResult] = []
        step_history: list[str | tuple[str, list[bytes]]] = []
        sequence_type = await self.plan_step_init(exec_context, screenshot)
        step_history.append(
            (
                "Orchestrator: Planned for test step "
                f"{exec_context.current_step[0]} => {exec_context.current_step[1]}"
            )
        )
        for i in range(4):
            logger.info(f"step #{exec_context.step_index}: processing iteration {i}")
            results = await self.execute_step(exec_context)
            success = not any(verdict.status != Status.PASS for verdict in results)
            if sequence_type == SequenceType.full and success:
                return TestStepVerdict(status=Status.PASS, history=step_history)
            workers_result = self._merge_worker_results(success, results)
            step_history.append(workers_result)
            if success:
                sequence_type = await self.plan_step_followup(workers_result)
                step_history.append("Orchestrator: Planned the step further")
            else:
                recovery = await self.plan_step_recover(workers_result)
                step_history.append("Orchestrator: Came up with a recovery solution")
                if not recovery:
                    return TestStepVerdict(status=Status.FAIL, history=step_history)
                else:
                    sequence_type = recovery
        return TestStepVerdict(status=Status.FAIL, history=step_history)

    async def plan_step_init(
        self, exec_context: TestExecutionContext, screenshot: bytes
    ) -> SequenceType:
        """Planning for the test step: spawn workers based on LLM call."""
        self._setup_conversation(exec_context, screenshot)
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

    async def plan_step_followup(
        self, workers_result: tuple[str, list[bytes]]
    ) -> SequenceType:
        """Continuing planning for the test step: spawn workers based on LLM call."""
        results_str, screenshots = workers_result
        with open(
            "./src/VTAAS/orchestrator/followup_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            results_str += prompt_file.read()

        user_msg = Message(
            role=MessageRole.User, content=results_str, screenshot=screenshots
        )
        self.conversation.append(user_msg)
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

    async def plan_step_recover(
        self, workers_result: tuple[str, list[bytes]]
    ) -> SequenceType | bool:
        """Recover planning of the test step: spawn workers based on LLM call."""
        results_str, screenshots = workers_result
        with open(
            "./src/VTAAS/orchestrator/recover_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            results_str += prompt_file.read()

        user_msg = Message(
            role=MessageRole.User, content=results_str, screenshot=screenshots
        )
        self.conversation.append(user_msg)
        response = await self.llm_client.recover_step(self.conversation)
        self.conversation.append(
            Message(
                role=MessageRole.Assistant,
                content=response.model_dump_json(),
            )
        )
        if not response.plan or not response.plan.workers:
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
        local_history: list[str] = []
        while self.active_workers and result.status == Status.PASS:
            worker = self.active_workers[0]
            input: WorkerInput = self._prepare_worker_input(
                exec_context, worker.type, local_history
            )
            result = await worker.process(input=input)
            if isinstance(result, ActorResult):
                for action in result.actions:
                    if action:
                        local_history.append(action.action)
            else:
                local_history.append(f'Verified: "{result.query}"')
            results.append(result)
            worker.status = WorkerStatus.RETIRED
            self.active_workers.remove(worker)
        self.active_workers.clear()
        return results

    async def step_synthesis(
        self,
        exec_context: TestExecutionContext,
        step_history: list[str | tuple[str, list[bytes]]],
        existing_synthesis: list[str],
    ) -> list[SynthesisEntry]:
        """Test step execution synthesis: keeping relevant info for future steps"""
        screenshots = [
            sshot
            for entry in step_history
            if isinstance(entry, tuple)
            for sshot in entry[1]
        ]
        system = "You are an expert in meaningful textual data extraction"
        synthesis = "\n".join(existing_synthesis)
        raw_step_history = "\n-----\n".join(
            [entry if isinstance(entry, str) else entry[0] for entry in step_history]
        )
        user = self._build_synthesis_prompt(exec_context, synthesis, raw_step_history)
        response = await self.llm_client.step_synthesis(system, user, screenshots)
        return response.entries

    def _merge_worker_results(
        self, success: bool, results: list[WorkerResult]
    ) -> tuple[str, list[bytes]]:
        outcome: str = "successfully" if success else "but eventually failed"
        merged_results: str = f"The sequence of workers was executed {outcome}:\n"
        screenshots: list[bytes] = []
        for result in results:
            screenshots.append(result.screenshot)
            if isinstance(result, ActorResult):
                actions_str = "\n".join(
                    [f"  - {action.chain_of_thought}" for action in result.actions]
                )
                merged_results += (
                    f'Act("{result.query}") -> {result.status.value}\n'
                    f"  Actions:\n{actions_str}\n"
                    "-----------------\n"
                )
            else:
                merged_results += (
                    f'Assert("{result.query}") -> {result.status.value}\n'
                    f"  Report: {result.synthesis}\n"
                    "-----------------\n"
                )
        return merged_results, screenshots

    def _prepare_worker_input(
        self,
        exec_context: TestExecutionContext,
        type: WorkerType,
        step_history: list[str],
    ) -> WorkerInput:
        full_history = ("\n").join(exec_context.synthesis + step_history)
        match type:
            case WorkerType.ACTOR:
                return ActorInput(
                    test_case=exec_context.test_case.__str__(),
                    test_step=exec_context.current_step,
                    history=full_history,
                )
            case WorkerType.ASSERTOR:
                return AssertorInput(
                    test_case=exec_context.test_case.__str__(),
                    test_step=exec_context.current_step,
                    history=full_history,
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

    def _build_synthesis_prompt(
        self,
        exec_context: TestExecutionContext,
        previous_synthesis: str,
        step_history: str,
    ) -> str:
        with open(
            "./src/VTAAS/orchestrator/synthesis_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()
        return prompt_template.format(
            test_case=exec_context.test_case,
            current_step=exec_context.current_step,
            saved_data=previous_synthesis,
            execution_logs=step_history,
        )

    def synthesis_str(self, synthesis: list[SynthesisEntry]):
        output: str = ""
        for entry in synthesis:
            output += " ----- \n"
            output += f"type: {entry.entry_type}\n"
            output += f"description: {entry.description}\n"
            output += f"value: {entry.value}\n"
        return output

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
