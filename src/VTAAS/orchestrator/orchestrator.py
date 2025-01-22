from typing import Any, Optional, Union

from VTAAS.data.testcase import TestCase
from VTAAS.workers.browser import Browser
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..workers.actor import Actor
from ..workers.observer import Observer
from ..schemas.worker import BaseWorker, WorkerStatus, WorkerType
from ..schemas.llm import LLMWorkerRequest

logger = get_logger(__name__)


class Orchestrator:
    """Orchestrator class to manage actors and observers."""

    def __init__(self):
        self.workers: list[BaseWorker] = []
        self.active_workers: list[BaseWorker] = []  # New list for active workers
        self.llm_client = LLMClient()
        self.browser = Browser("1", True)
        self.worker_counter: dict[str, int] = {"actor": 0, "observer": 0}
        logger.info("Orchestrator initialized")

    def get_main_prompt(self, action: str, assertion: str) -> str:
        return f"action: {action}, assertion: {assertion}"

    async def process_TestCase(self, test_case: TestCase) -> None:
        """Manages the main execution loop for the given Test Case."""

        logger.info(f"Processing {test_case.name}")

        # Iterating over all actions and assertions till the end of the TC
        for i in range(len(test_case)):
            current_action = test_case.actions[i]
            current_assertion = test_case.expected_results[i]

            # Placeholder for the call to the browser to get initial screenshot:
            #
            #
            #
            screenshot = "I am a screenshot in disguise"

            await self.initialize_workers(
                self.get_main_prompt(current_action, current_assertion), screenshot
            )

            await self.process()

    async def initialize_workers(self, prompt: str, screenshot: Optional[str]):
        """Initialise workers based on LLM call."""
        request = LLMWorkerRequest(prompt=prompt, screenshot=screenshot)

        # Get worker configurations from LLM
        worker_configs = await self.llm_client.get_worker_configs(request)

        # Spawn workers based on configurations
        for config in worker_configs:
            self.spawn_worker(config)

        logger.info(f"Initialized {len(self.active_workers)} new workers")

    def spawn_worker(self, config: BaseWorker) -> Union[Actor, Observer]:
        """Spawn a new worker based on the provided configuration."""
        if config.type == WorkerType.ACTOR:
            worker = Actor(config, self.browser)
            self.workers.append(worker)
            self.active_workers.append(worker)
        else:
            worker = Observer(config, self.browser)
            self.workers.append(worker)
            self.active_workers.append(worker)
        return worker

    async def process(self) -> list[Any]:
        """
        Process only active workers and retire them after processing.
        """
        results = []
        for worker in self.active_workers[:]:  # Create a copy of the list to iterate
            result = await worker.process()
            results.append(result)
            worker.status = WorkerStatus.RETIRED
            self.active_workers.remove(worker)
        return results
