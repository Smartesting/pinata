from typing import TypeGuard, final, override

from VTAAS.llm.llm_client import LLMProviders
from VTAAS.llm.utils import create_llm_client
from VTAAS.utils.banner import add_banner
from VTAAS.utils.logger import get_logger

from ..schemas.verdict import AssertorResult
from ..workers.browser import Browser
from ..schemas.worker import (
    AssertorInput,
    Message,
    MessageRole,
    Worker,
    WorkerInput,
    WorkerType,
)


@final
class Assertor(Worker):
    """Assertor implementation."""

    def __init__(
        self,
        query: str,
        browser: Browser,
        llm_provider: LLMProviders,
        start_time: float,
    ):
        super().__init__(query, browser)
        self.type = WorkerType.ASSERTOR
        self.start_time = start_time
        self.llm_client = create_llm_client(llm_provider, start_time)
        self.logger = get_logger("Assertor " + self.id[:8], self.start_time)
        self.logger.info(f"initialized with query: {self.query}")

    @override
    async def process(self, input: WorkerInput) -> AssertorResult:
        if not self._is_assertor_input(input):
            raise TypeError("Expected input of type AssertorInput")
        screenshot = await self.browser.screenshot()
        self._setup_conversation(input, screenshot)
        self.logger.info(f"\n\nprocessing query '{self.query}'")
        response = await self.llm_client.assert_(self.conversation)
        return AssertorResult(
            query=self.query,
            status=response.verdict.status,
            synthesis=response.get_cot(),
            screenshot=add_banner(screenshot, f'assert("{self.query}"'),
        )

    @property
    def system_prompt(self) -> str:
        return "You are part of a multi-agent systems. Your role is to assert the expected state of a web application, given a query."

    def _setup_conversation(self, input: AssertorInput, screenshot: bytes):
        self.conversation = [
            Message(role=MessageRole.System, content=self.system_prompt),
            Message(
                role=MessageRole.User,
                content=self._build_user_prompt(input),
                screenshot=[screenshot],
            ),
        ]
        self.logger.debug(f"User prompt:\n\n{self.conversation[1].content}")

    def _build_user_prompt(self, input: AssertorInput) -> str:
        with open(
            "./src/VTAAS/workers/assertor_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()

        current_step = input.test_step[0] + "; " + input.test_step[1]

        return prompt_template.format(
            test_case=input.test_case,
            current_step=current_step,
            assertion=self.query,
        )

    def _is_assertor_input(self, input: WorkerInput) -> TypeGuard[AssertorInput]:
        return isinstance(input, AssertorInput)

    @override
    def __str__(self) -> str:
        return f"Assert({self.query})"
