from typing import Any
from uuid import uuid4

from VTAAS.workers.browser import Browser
from ..utils.logger import get_logger
from ..schemas.worker import BaseWorker
import asyncio

logger = get_logger(__name__)


class Observer:
    """Observer implementation."""

    def __init__(self, config: BaseWorker, browser: Browser):
        self.config = config
        # self.name = config.name
        self.id = uuid4().hex
        self.query = config.query
        self.browser = browser
        # self.interval = config.observation_interval
        logger.info(f"Observer {self.id} initialized with query: {self.query}")

    async def process(self) -> Any:
        """Process the given data asynchronously."""
        logger.info(f"Observer {self.id} processing data")

        # Simulate some async work for now
        await asyncio.sleep(0.1)

        return {
            "worker_type": "observer",
            "id": self.id,
            "query": self.query,
            "observation": "Observed: something",
            # "interval": self.interval,
        }
