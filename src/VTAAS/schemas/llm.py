from pydantic import BaseModel, Field
from .worker_schemas import (
    BaseWorker,
)


class LLMWorkerRequest(BaseModel):
    """Schema for the request sent to LLM."""

    context: str = Field(..., description="Context of the task to be performed")
    objective: str = Field(..., description="Main objective to be achieved")


class LLMWorkerResponse(BaseModel):
    """Schema for the response received from LLM."""

    workers: list[BaseWorker]

    # @field_validator("workers")
    # def validate_workers(cls, workers):
    #     validated_workers = []
    #     for worker in workers:
    #         # Ensure type field exists
    #         if "type" not in worker:
    #             raise ValueError("Worker must have a 'type' field")
    #         if "query" not in worker:
    #             raise ValueError("Worker must have a 'query' field")

    #         # Convert to appropriate worker type
    #         if worker["type"] == WorkerType.ACTOR:
    #             validated_worker = ActorWorker(**worker)
    #         elif worker["type"] == WorkerType.OBSERVER:
    #             validated_worker = ObserverWorker(**worker)
    #         else:
    #             raise ValueError(f"Invalid worker type: {worker['type']}")

    #         validated_workers.append(validated_worker)
    #     return validated_workers
