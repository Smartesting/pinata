from enum import Enum
from typing import TypedDict
from pydantic import BaseModel, Field
from ..schemas.verdict import WorkerVerdict
import abc


class WorkerType(str, Enum):
    ACTOR = "actor"
    OBSERVER = "observer"


class WorkerStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class WorkerConfig(TypedDict):
    type: WorkerType
    query: str


class BaseWorker(BaseModel):
    """Base worker schema with common attributes."""

    type: WorkerType
    status: WorkerStatus = Field(default=WorkerStatus.ACTIVE)

    @abc.abstractmethod
    async def process(self) -> WorkerVerdict: ...

    # id: str = Field(default_factory=lambda: uuid4().hex)
    query: str  # = Field(..., description="Task description or query to be executed")
