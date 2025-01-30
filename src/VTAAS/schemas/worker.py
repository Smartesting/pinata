from enum import Enum
from uuid import uuid4

from pydantic import BaseModel

from VTAAS.workers.browser import Browser
from ..schemas.verdict import WorkerResult
from abc import ABC, abstractmethod


class MessageRole(str, Enum):
    System = "system"
    User = "user"
    Assistant = "assistant"


class Message(BaseModel):
    role: MessageRole
    content: str
    screenshot: list[bytes] | None = None

    class Config:
        use_enum_values: bool = True


class WorkerType(str, Enum):
    ACTOR = "act"
    ASSERTOR = "assert"


class WorkerStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class WorkerConfig(BaseModel):
    type: WorkerType
    query: str


class ActorInput(BaseModel):
    test_case: str
    test_step: tuple[str, str]
    history: str | None


class AssertorInput(BaseModel):
    test_case: str
    test_step: tuple[str, str]
    history: str | None


WorkerInput = ActorInput | AssertorInput


class AssertionChecking(BaseModel):
    observation: str
    verification: str


class Worker(ABC):
    """Abstract worker with common attributes."""

    type: WorkerType

    def __init__(self, query: str, browser: Browser):
        self.status: WorkerStatus = WorkerStatus.ACTIVE
        self.query: str = query
        self.id: str = uuid4().hex
        self.browser: Browser = browser
        self.conversation: list[Message] = []

    @abstractmethod
    async def process(self, input: WorkerInput) -> WorkerResult: ...
