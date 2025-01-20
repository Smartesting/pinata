import asyncio
from typing import Any, dict, list

from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..workers.actor import Actor
from ..workers.observer import Observer

logger = get_logger(__name__)


class Orchestrator:
    """Orchestrator class to manage actors and observers."""

    def __init__(self, llm_api_key: str | None = None):
        self.actors: list[Actor] = []
        self.observers: list[Observer] = []
        self.llm_client = LLMClient(api_key=llm_api_key)
        self.worker_counter: dict[str, int] = {"actor": 0, "observer": 0}
        logger.info("Orchestrator initialized")

    def spawn_actor(self, name: str) -> Actor:
        """Spawn a new Actor instance."""
        actor = Actor(name)
        self.actors.append(actor)
        logger.info(f"Spawned Actor: {name}")
        return actor

    def spawn_observer(self, name: str) -> Observer:
        """Spawn a new Observer instance."""
        observer = Observer(name)
        self.observers.append(observer)
        logger.info(f"Spawned Observer: {name}")
        return observer

    async def spawn_and_process(self, context: str, data: Any) -> list[Any]:
        """
        Get roles from LLM, spawn corresponding workers, and process data.
        """
        # Get roles from LLM
        roles = await self.llm_client.get_roles(context)
        logger.info(f"Received roles from LLM: {roles}")

        # Create tasks list for processing
        tasks = []

        # Spawn workers based on roles and create their tasks
        for role in roles:
            if role == "actor":
                self.worker_counter["actor"] += 1
                actor = self.spawn_actor(f"actor_{self.worker_counter['actor']}")
                tasks.append(actor.process(data))
            elif role == "observer":
                self.worker_counter["observer"] += 1
                observer = self.spawn_observer(
                    f"observer_{self.worker_counter['observer']}"
                )
                tasks.append(observer.process(data))
            else:
                logger.warning(f"Unknown role received: {role}")

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        return results
