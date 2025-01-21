from enum import Enum
from pydantic import BaseModel


class WorkerType(str, Enum):
    ACTOR = "actor"
    OBSERVER = "observer"


class BaseWorker(BaseModel):
    """Base worker schema with common attributes."""

    type: WorkerType
    # id: str = Field(default_factory=lambda: uuid4().hex)
    query: str  # = Field(..., description="Task description or query to be executed")


# class ActorWorker(BaseWorker):
#     """Schema for workers that execute test case actions."""

#     type: WorkerType = Field(default=WorkerType.ACTOR)
#     # action_priority: Optional[int] = Field(
#     #     default=1, description="Priority level for the action (1-5)", ge=1, le=5
#     # )


# class ObserverWorker(BaseWorker):
#     """Schema for workers that check for assertions."""

#     type: WorkerType = Field(default=WorkerType.OBSERVER)
#     # observation_interval: Optional[float] = Field(
#     #     default=1.0, description="Interval in seconds between observations"
#     # )


# WorkerSchema = Union[ActorWorker, ObserverWorker]
