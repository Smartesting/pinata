from typing import Any
import asyncio
from uuid import uuid4

from VTAAS.workers.browser import Browser

from ..schemas.worker import BaseWorker
from ..utils.logger import get_logger

# from ..schemas.worker_schemas import ActorWorker

logger = get_logger(__name__)


class Actor:
    """Actor implementation."""

    def __init__(self, config: BaseWorker, browser: Browser):
        self.config = config
        self.id = uuid4().hex
        self.query = config.query
        self.browser = browser
        # self.priority = config.action_priority
        # self.can_modify = config.can_modify
        logger.info(f"Actor {self.id} initialized with query: {self.query}")

    async def process(self) -> Any:
        """Process the given data asynchronously."""
        logger.info(f"Actor {self.id} processing data")

        # Simulate some async work for now
        await asyncio.sleep(0.1)

        return {
            "worker_type": "actor",
            "id": self.id,
            "query": self.query,
            "result": "Processed: something",
            # "modified": self.can_modify,
        }
