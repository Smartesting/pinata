from typing import List
import asyncio
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Skeleton LLM client."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    async def get_roles(self, context: str) -> List[str]:
        """
        Simulate an LLM call that returns a list of 'actor' or 'observer' strings.
        In real implementation, this would make an actual API call to an LLM.
        """
        logger.info("Making LLM API call for role determination")
        # Simulate API latency
        await asyncio.sleep(1)

        # Dummy response - in real implementation, this would be the LLM's output
        return ["actor", "observer", "actor", "observer"]
