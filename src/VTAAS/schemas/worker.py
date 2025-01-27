from enum import Enum
from typing import TypedDict
from uuid import uuid4

from VTAAS.workers.browser import Browser
from ..schemas.verdict import WorkerVerdict
from abc import ABC, abstractmethod


class WorkerType(str, Enum):
    ACTOR = "act"
    ASSERTOR = "assert"


class WorkerStatus(str, Enum):
    ACTIVE = "active"
    RETIRED = "retired"


class WorkerConfig(TypedDict):
    type: WorkerType
    query: str


class Worker(ABC):
    """Abstract worker with common attributes."""

    def __init__(self, query: str, browser: Browser):
        self.status: WorkerStatus = WorkerStatus.ACTIVE
        self.query: str = query
        self.id: str = uuid4().hex
        self.browser: Browser = browser

    @abstractmethod
    async def process(self) -> WorkerVerdict: ...
