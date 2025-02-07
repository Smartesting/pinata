from enum import Enum
from typing import Protocol

from ..schemas.worker import Message
from ..schemas.llm import (
    LLMActResponse,
    LLMAssertResponse,
    LLMSynthesisResponse,
    LLMTestStepFollowUpResponse,
    LLMTestStepPlanResponse,
    LLMTestStepRecoverResponse,
)

from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient(Protocol):
    async def plan_step(
        self, conversation: list[Message]
    ) -> LLMTestStepPlanResponse: ...

    async def followup_step(
        self, conversation: list[Message]
    ) -> LLMTestStepFollowUpResponse: ...

    async def recover_step(
        self, conversation: list[Message]
    ) -> LLMTestStepRecoverResponse: ...

    async def act(self, conversation: list[Message]) -> LLMActResponse: ...

    async def assert_(self, conversation: list[Message]) -> LLMAssertResponse: ...

    async def step_synthesis(
        self, system: str, user: str, screenshots: list[bytes]
    ) -> LLMSynthesisResponse: ...


class LLMProviders(str, Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
