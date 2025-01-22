import asyncio
from uuid import uuid4

from VTAAS.schemas.verdict import Status, StepVerdict
from VTAAS.workers.browser import Browser

from ..schemas.worker import BaseWorker
from ..utils.logger import get_logger

# from ..schemas.worker_schemas import ActorWorker

logger = get_logger(__name__)


class Actor(BaseWorker):
    """Actor implementation."""

    def __init__(self, config: BaseWorker, browser: Browser):
        self.config = config
        self.id = uuid4().hex
        self.query = config.query
        self.browser = browser
        # self.priority = config.action_priority
        # self.can_modify = config.can_modify
        logger.info(f"Actor {self.id} initialized with query: {self.query}")

    async def process(self) -> StepVerdict:
        """Process the given data asynchronously."""
        logger.info(f"Actor {self.id} processing data")

        # Simulate some async work for now
        await asyncio.sleep(0.1)

        verdict = StepVerdict(status=Status.PASS, explaination="see that later")

        return verdict
