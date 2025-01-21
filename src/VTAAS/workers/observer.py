from typing import Any
from uuid import uuid4
from ..utils.logger import get_logger
from ..schemas.worker import BaseWorker
import asyncio

logger = get_logger(__name__)


class Observer:
    """Observer implementation."""

    def __init__(self, config: BaseWorker):
        self.config = config
        # self.name = config.name
        self.id = uuid4().hex
        self.query = config.query
        # self.interval = config.observation_interval
        logger.info(f"Observer {self.id} initialized with query: {self.query}")

    async def process(self, data: Any) -> Any:
        """Process the given data asynchronously."""
        logger.info(f"Observer {self.id} processing data")

        # Simulate some async work for now
        await asyncio.sleep(1)

        return {
            "worker_type": "observer",
            "id": self.id,
            "query": self.query,
            "observation": f"Observed: {data}",
            # "interval": self.interval,
        }
