from typing import final, override
from uuid import uuid4

from VTAAS.schemas.llm import LLMRequest
from VTAAS.schemas.verdict import Status, WorkerVerdict
from VTAAS.utils.llm_client import LLMClient
from VTAAS.workers.browser import Browser
from ..utils.logger import get_logger
from ..schemas.worker import Worker, WorkerType

logger = get_logger(__name__)


@final
class Assertor(Worker):
    """Assertor implementation."""

    def __init__(self, query: str, browser: Browser):
        super().__init__(query, browser)
        self.type = WorkerType.ASSERTOR
        self.llm_client = LLMClient()
        # self.priority = config.action_priority
        # self.can_modify = config.can_modify
        logger.info(f"Actor {self.id} initialized with query: {self.query}")

    @override
    async def process(self) -> WorkerVerdict:
        """Process the given data asynchronously."""
        screenshot = await self.browser.screenshot()

        request = LLMRequest(
            prompt=(self.system_prompt, self.query), screenshot=screenshot
        )
        _ = await self.llm_client.get_step_verdict(request)
        logger.info(f"Actor {self.id} processing data")
        verdict: WorkerVerdict = await self.llm_client.get_step_verdict(request)

        verdict = WorkerVerdict(status=Status.PASS, explaination="see that later")

        return verdict

    @property
    def system_prompt(self) -> str:
        return "You are part of a multi-agent systems. Your role is to verify information on a web application"
