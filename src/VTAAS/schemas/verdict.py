from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field


class Status(str, Enum):
    PASS = "success"
    FAIL = "fail"
    UNK = "unknown"


class BaseResult(BaseModel):
    """Base result schema"""

    status: Status = Field(..., description="Status of the result")
    explaination: str | None = None

    class Config:
        use_enum_values: bool = True


class WorkerBaseResult(BaseModel):
    """Worker Base result schema"""

    query: str
    status: Status = Field(..., description="Status of the result")
    explaination: str | None = None
    screenshot: bytes


class ActorAction(BaseModel):
    action: str
    chain_of_thought: str


class ActorResult(WorkerBaseResult):
    actions: list[ActorAction]


class AssertorResult(WorkerBaseResult):
    synthesis: str


class TestCaseVerdict(BaseResult): ...


WorkerResult = ActorResult | AssertorResult


class AssertionVerdict(BaseModel):
    status: Status = Field(..., description="Verdict Status")
    discrepancies: str = None  # noqa
