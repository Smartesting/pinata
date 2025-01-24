from ..data.testcase import TestCase
from ..schemas.verdict import CaseVerdict, Status, WorkerVerdict
from ..workers.browser import Browser
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..workers.actor import Actor
from ..workers.observer import Observer
from ..schemas.worker import BaseWorker, WorkerStatus, WorkerType
from ..schemas.llm import LLMRequest

logger = get_logger(__name__)


class Orchestrator:
    """Orchestrator class to manage actors and observers."""

    def __init__(self):
        self.workers: list[BaseWorker] = []
        self.active_workers: list[BaseWorker] = []
        self.llm_client: LLMClient = LLMClient()
        self.browser: Browser = Browser()
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
        url = "http://wwww.vtaas-browser.com"
        _ = await self.browser.goto(url)
        # Iterating over all actions and assertions till the end of the TC
        # First iteration of VTAAS allows only one shot for each tuple action + assertion
        results: list[WorkerVerdict] = []
        for i in range(len(test_case)):
            # action, assertion = test_case.get_step(i)
            screenshot = b""
            screenshotResult = await self.browser.screenshot()
            if "screenshot" in screenshotResult:
                screenshot = screenshotResult["screenshot"]

            await self.initialize_workers(
                self.get_main_prompt(i),
                screenshot,
            )

            results = await self.process()

        if all(verdict.status == Status.PASS for verdict in results):
            return CaseVerdict(status=Status.PASS, explaination=None)
        else:
            return CaseVerdict(status=Status.FAIL, explaination=None)

        # Placeholder for the call to the LLM to give a verdict for the case:
        #
        #
        #

    async def initialize_workers(
        self, prompt: tuple[str, str], screenshot: bytes | None = None
    ):
        """Planning for the test step: initialise workers based on LLM call."""
        request = LLMRequest(prompt=prompt, screenshot=screenshot)

        # Get worker configurations from LLM
        worker_configs = await self.llm_client.get_worker_configs(request)

        # Spawn workers based on configurations
        for config in worker_configs:
            _ = self.spawn_worker(config)

        logger.info(f"Initialized {len(self.active_workers)} new workers")

    def spawn_worker(self, config: BaseWorker) -> BaseWorker:
        """Spawn a new worker based on the provided configuration."""
        worker: BaseWorker
        match config.type:
            case WorkerType.ACTOR:
                worker = Actor(config, self.browser)
                self.workers.append(worker)
                self.active_workers.append(worker)
            case WorkerType.OBSERVER:
                worker = Observer(config, self.browser, self.llm_client)
                self.workers.append(worker)
                self.active_workers.append(worker)
        return worker

    async def process(self) -> list[WorkerVerdict]:
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

    def _get_system_prompt(self) -> str:
        with open("system_prompt.txt", "r", encoding="utf-8") as prompt_file:
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
