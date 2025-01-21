from typing import Any
import asyncio
from uuid import uuid4

from ..schemas.worker_schemas import BaseWorker
from ..utils.logger import get_logger

# from ..schemas.worker_schemas import ActorWorker

logger = get_logger(__name__)


class Actor:
    """Actor implementation."""

    def __init__(self, config: BaseWorker):
        self.config = config
        self.id = uuid4().hex
        self.query = config.query
        # self.priority = config.action_priority
        # self.can_modify = config.can_modify
        logger.info(f"Actor {self.id} initialized with query: {self.query}")

    async def process(self, data: Any) -> Any:
        """Process the given data asynchronously."""
        logger.info(f"Actor {self.id} processing data")

        # Simulate some async work for now
        await asyncio.sleep(3)

        return {
            "worker_type": "actor",
            "id": self.id,
            "query": self.query,
            "result": f"Processed: {data}",
            # "modified": self.can_modify,
        }
