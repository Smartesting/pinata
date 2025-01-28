from typing import final, override

from ..schemas.llm import LLMRequest
from ..schemas.verdict import Status, WorkerResult
from ..utils.llm_client import LLMClient
from ..workers.browser import Browser
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
    async def process(self) -> WorkerResult:
        """Process the given data asynchronously."""
        screenshot = await self.browser.screenshot()
        request = LLMRequest(
            prompt=(self.system_prompt, self.query), screenshot=screenshot
        )
        _ = await self.llm_client.get_step_verdict(request)
        logger.info(f"Actor {self.id} processing data")
        verdict: WorkerResult = await self.llm_client.get_step_verdict(request)
        verdict = WorkerResult(status=Status.PASS, explaination="see that later")
        return verdict

    @override
    def get_prompt(self) -> tuple[str, str]:
        user_prompt = self._build_user_prompt("test_case", "step", "history")
        return (self.system_prompt, user_prompt)

    @property
    def system_prompt(self) -> str:
        return "You are part of a multi-agent systems. Your role is to assert the expected state of a web application"

    def _build_user_prompt(self, test_case, step_index, history) -> str:
        with open(
            "./src/VTAAS/workers/assertor_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()

        return prompt_template.format(
            test_case=test_case, current_step=test_step, history=history
        )
