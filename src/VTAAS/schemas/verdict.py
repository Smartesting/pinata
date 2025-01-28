from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    PASS = "success"
    FAIL = "fail"
    UNK = "unknown"


class BaseResult(BaseModel):
    """Base result schema"""

    status: Status = Field(..., description="Status of the result")
    explaination: str | None


class WorkerResult(BaseResult): ...


class TestCaseVerdict(BaseResult): ...


Verdict = WorkerResult | TestCaseVerdict
