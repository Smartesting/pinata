from typing import Any
import asyncio
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Actor:
    """Actor implementation."""

    def __init__(self, name: str):
        self.name = name
        logger.info(f"Actor {self.name} initialized")

    async def process(self, data: Any) -> Any:
        """Process the given data asynchronously."""
        logger.info(f"Actor {self.name} processing data")

        # Simulate some async work for now
        await asyncio.sleep(3)

        return f"Actor {self.name} processed: {data}"
