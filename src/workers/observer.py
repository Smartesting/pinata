from typing import Any
from ..utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


class Observer:
    """Observer implementation."""

    def __init__(self, name: str):
        self.name = name
        logger.info(f"Observer {self.name} initialized")

    async def process(self, data: Any) -> Any:
        """Process the given data asynchronously."""
        logger.info(f"Observer {self.name} processing data")

        # Simulate some async work for now
        await asyncio.sleep(1)

        return f"Observer {self.name} processed: {data}"
