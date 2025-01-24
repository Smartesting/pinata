from VTAAS.schemas.verdict import WorkerVerdict
from pydantic import BaseModel, Field
from .worker import (
    BaseWorker,
)


class LLMRequest(BaseModel):
    """Schema for the request sent to LLM."""

    prompt: tuple[str, str] = Field(
        ..., description="Prompt for the request to the LLM"
    )  # noqa
    screenshot: bytes | None = Field(..., description="Main objective to be achieved")


class LLMWorkerResponse(BaseModel):
    """Schema for the response received from LLM."""

    workers: list[BaseWorker]


class LLMVerdictResponse(BaseModel):
    """Schema for the response received from LLM."""

    verdict: WorkerVerdict
