from typing import Any, Union
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..workers.actor import Actor
from ..workers.observer import Observer
from ..schemas.worker_schemas import BaseWorker, WorkerType
from ..schemas.llm_schemas import LLMWorkerRequest

logger = get_logger(__name__)


class Orchestrator:
    """Orchestrator class to manage actors and observers."""

    def __init__(self):
        self.workers: list[BaseWorker] = []
        self.actors: list[Actor] = []
        self.observers: list[Observer] = []
        self.llm_client = LLMClient()
        self.worker_counter: dict[str, int] = {"actor": 0, "observer": 0}
        logger.info("Orchestrator initialized")

    async def initialize_workers(self, context: str, objective: str):
        """Initialise workers based on LLM response."""
        request = LLMWorkerRequest(context=context, objective=objective)

        # Get worker configurations from LLM
        worker_configs = await self.llm_client.get_worker_configs(request)

        # Spawn workers based on configurations
        for config in worker_configs:
            self.spawn_worker(config)

        logger.info(
            f"Initialized {len(self.actors)} actors and {len(self.observers)} observers"
        )

    def spawn_worker(self, config: BaseWorker) -> Union[Actor, Observer]:
        """Spawn a new worker based on the provided configuration."""
        if config.type == WorkerType.ACTOR:
            worker = Actor(config)
            self.workers.append(worker)
            self.actors.append(worker)
            # logger.info(f"Spawned Actor: {config.name}")
        else:
            worker = Observer(config)
            self.workers.append(worker)
            self.observers.append(worker)
            # logger.info(f"Spawned Observer: {config.name}")
        return worker

    async def spawn_and_process(self, context: str, data: Any) -> list[Any]:
        """
        Get roles from LLM, spawn corresponding workers, and process data.
        """
        # Get roles from LLM
        # roles = await self.llm_client.get_roles(context)
        # logger.info(f"Received roles from LLM: {roles}")

        # Create tasks list for processing
        # tasks = []

        # Spawn workers based on roles and create their tasks
        # for actor in self.actors:
        #     if isinstance(actor, Actor):
        #         self.worker_counter["actor"] += 1
        #         tasks.append(actor.process(data))
        #     elif isinstance(actor, Observer()):
        #         self.worker_counter["observer"] += 1
        #         observer = self.spawn_observer(
        #             f"observer_{self.worker_counter['observer']}"
        #         )
        #         tasks.append(observer.process(data))

        # Wait for all tasks to complete
        # results = await asyncio.gather(*tasks)

        # Version where the different workers are executed sequentially
        results = [await task for task in [x.process(data) for x in self.workers]]
        return results
