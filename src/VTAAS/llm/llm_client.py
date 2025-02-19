from enum import Enum
from typing import Protocol

from ..schemas.worker import Message
from ..schemas.llm import (
    LLMActResponse,
    LLMAssertResponse,
    LLMDataExtractionResponse,
    LLMTestStepFollowUpResponse,
    LLMTestStepPlanResponse,
    LLMTestStepRecoverResponse,
)


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

    async def step_postprocess(
        self, system: str, user: str, screenshots: list[bytes]
    ) -> LLMDataExtractionResponse: ...


class LLMProvider(str, Enum):
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    MISTRAL = "mistral"
