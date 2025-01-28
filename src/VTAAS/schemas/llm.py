from enum import Enum

from pydantic import BaseModel, Field

from ..schemas.verdict import Verdict, WorkerResult
from .worker import (
    AssertionChecking,
    Command,
    WorkerConfig,
)


class SequenceType(Enum):
    full = 1
    partial = 2


class LLMRequest(BaseModel):
    """Schema for the request sent to LLM."""

    prompt: tuple[str, str] = Field(
        ..., description="Prompt for the request to the LLM"
    )  # noqa
    screenshot: bytes | None = Field(..., description="Main objective to be achieved")


class LLMTestStepPlanResponse(BaseModel):
    """Schema for the response received from LLM."""

    current_step_analysis: str
    screenshot_analysis: str
    previous_actions_analysis: str
    workers: list[WorkerConfig]
    sequence_type: SequenceType


class LLMActResponse(BaseModel):
    """Schema for the response received from LLM."""

    current_webpage_identification: str
    screenshot_analysis: str
    next_action: str
    command: Command


class LLMAssertResponse(BaseModel):
    """Schema for the response received from LLM."""

    page_description: str
    assertion_checking: AssertionChecking
    verdict: Verdict


class LLMVerdictResponse(BaseModel):
    """Schema for the response received from LLM."""

    verdict: WorkerResult
