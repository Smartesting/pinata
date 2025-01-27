from ..data.testcase import TestCase
from ..schemas.verdict import CaseVerdict, Status, WorkerVerdict
from ..workers.browser import Browser
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..workers.actor import Actor
from ..workers.observer import Assertor
from ..schemas.worker import Worker, WorkerConfig, WorkerStatus, WorkerType
from ..schemas.llm import LLMRequest

logger = get_logger(__name__)


class Orchestrator:
    """Orchestrator class to manage actors and observers."""

    def __init__(self):
        self.workers: list[Worker] = []
        self.active_workers: list[Worker] = []
        self.llm_client: LLMClient = LLMClient()
        self._browser: Browser | None = None
        self.test_case: TestCase | None = None
        self.worker_reports: dict[str, list[str]] = {}
        self.worker_counter: dict[str, int] = {"actor": 0, "observer": 0}
        logger.info("Orchestrator initialized")

    def get_main_prompt(
        self, test_step_index: int, history: str | None = None
    ) -> tuple[str, str]:
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(test_step_index, history)
        return (system_prompt, user_prompt)

    def get_verdict_prompt(self, result: list[WorkerVerdict], assertion: str) -> str:
        return f"action: {result}, assertion: {assertion}"

    async def process_TestCase(self, test_case: TestCase) -> CaseVerdict:
        """Manages the main execution loop for the given Test Case."""

        logger.info(f"Processing {test_case.name}")
        self.test_case = test_case
        url = "http://www.vtaas-benchmark.com:9999/"
        self._browser = await Browser.create(timeout=3500, headless=True)
        _ = await self.browser.goto(url)
        # Iterating over all actions and assertions till the end of the TC
        # First iteration of VTAAS allows only one shot for each tuple action + assertion
        results: list[WorkerVerdict] = []
        for i in range(len(test_case)):
            # action, assertion = test_case.get_step(i)
            screenshot = await self.browser.screenshot()

            await self.plan(
                self.get_main_prompt(i),
                screenshot,
            )

            results = await self.execute()

        if all(verdict.status == Status.PASS for verdict in results):
            return CaseVerdict(status=Status.PASS, explaination=None)
        else:
            return CaseVerdict(status=Status.FAIL, explaination=None)

    async def plan(self, prompt: tuple[str, str], screenshot: bytes | None = None):
        """Planning for the test step: spawn workers based on LLM call."""
        request = LLMRequest(prompt=prompt, screenshot=screenshot)
        worker_configs = await self.llm_client.plan_for_step(request)
        for config in worker_configs:
            _ = self.spawn_worker(config)
        logger.info(f"Initialized {len(self.active_workers)} new workers")

    async def execute(self) -> list[WorkerVerdict]:
        """
        Process only active workers and retire them after processing.
        """
        results: list[WorkerVerdict] = []
        for worker in self.active_workers[:]:  # Create a copy of the list to iterate
            result = await worker.process()
            results.append(result)
            worker.status = WorkerStatus.RETIRED
            self.active_workers.remove(worker)
        return results

    def spawn_worker(self, config: WorkerConfig) -> Worker:
        """Spawn a new worker based on the provided configuration."""
        worker: Worker
        match config["type"]:
            case WorkerType.ACTOR:
                worker = Actor(config["query"], self.browser)
                self.workers.append(worker)
                self.active_workers.append(worker)
            case WorkerType.ASSERTOR:
                worker = Assertor(config["query"], self.browser)
                self.workers.append(worker)
                self.active_workers.append(worker)
        return worker

    def _get_system_prompt(self) -> str:
        with open(
            "./src/VTAAS/orchestrator/system_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()
        return prompt_template

    def _get_user_prompt(self, test_step_index: int, history: str | None = None) -> str:
        with open(
            "./src/VTAAS/orchestrator/prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()
        test_case = "blablabla"
        action = "Login as superuser/trial"
        assertion = "Logged in as admin"
        test_step = f"{test_step_index}. action: {action}, assertion: {assertion}"
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
