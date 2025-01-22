from enum import Enum
from typing import Union
from pydantic import BaseModel, Field


class Status(str, Enum):
    PASS = "success"
    FAIL = "fail"
    UNK = "unknown"


class BaseVerdict(BaseModel):
    """Verdict schema"""

    status: Status = Field(..., description="Status of the verdict")
    explaination: str | None


class StepVerdict(BaseVerdict): ...


class CaseVerdict(BaseVerdict): ...


Verdict = Union[StepVerdict, CaseVerdict]
