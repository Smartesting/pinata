from enum import Enum
from VTAAS.schemas.verdict import WorkerVerdict
from pydantic import BaseModel, Field
from .worker import (
    Worker,
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


class LLMWorkerResponse(BaseModel):
    """Schema for the response received from LLM."""

    current_step_analysis: str
    screenshot_analysis: str
    previous_actions_analysis: str
    workers: list[WorkerConfig]
    sequence_type: SequenceType


class LLMVerdictResponse(BaseModel):
    """Schema for the response received from LLM."""

    verdict: WorkerVerdict
