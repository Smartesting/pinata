from uuid import uuid4

from VTAAS.schemas.llm import LLMRequest
from VTAAS.schemas.verdict import WorkerVerdict
from VTAAS.utils.llm_client import LLMClient
from VTAAS.workers.browser import Browser
from ..utils.logger import get_logger
from ..schemas.worker import BaseWorker

logger = get_logger(__name__)


class Observer(BaseWorker):
    """Observer implementation."""

    def __init__(self, config: BaseWorker, browser: Browser, llm_client: LLMClient):
        self.config = config
        self.id = uuid4().hex
        self.llm_client = llm_client
        self.query = config.query
        self.browser = browser
        logger.info(f"Observer {self.id} initialized with query: {self.query}")

    async def process(self) -> WorkerVerdict:
        """Process the given data asynchronously."""
        logger.info(f"Observer {self.id} processing data")

        screenshot = "This is a screenshot for now"

        request = LLMRequest(prompt=self.query, screenshot=screenshot)

        # Simulate some async work for now
        # await asyncio.sleep(0.1)
        verdict: WorkerVerdict = await self.llm_client.get_step_verdict(request)
        return verdict
