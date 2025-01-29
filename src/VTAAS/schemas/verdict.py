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
    explaination: str | None


class ActorAction(TypedDict):
    action: str
    outcome: str


class AssertorResult(BaseResult):
    synthesis: str


class ActorResult(BaseResult):
    actions: list[ActorAction]


class TestCaseVerdict(BaseResult): ...


WorkerResult = ActorResult | AssertorResult
Verdict = WorkerResult | TestCaseVerdict
