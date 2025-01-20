from typing import List
import asyncio
from openai import OpenAI, OpenAIError
from ..utils.logger import get_logger
from ..utils.config import load_config
import sys

logger = get_logger(__name__)


class LLMClient:
    """Skeleton LLM client."""

    def __init__(self):
        # Load environment variables
        load_config()

        logger.info("Connection to OpenAI ...")

        try:
            self.client = OpenAI()

        except OpenAIError as e:
            logger.fatal(e, exc_info=True)
            sys.exit(1)

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
