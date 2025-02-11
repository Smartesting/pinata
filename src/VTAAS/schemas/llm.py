import ast
from enum import Enum
from typing import Literal

from google.genai.types import Schema
from pydantic import BaseModel, Field


from ..schemas.verdict import AssertionVerdict, Status, WorkerResult
from .worker import (
    AssertionChecking,
    WorkerConfig,
)


class SequenceType(str, Enum):
    full = "full"
    partial = "partial"


class LLMRequest(BaseModel):
    """Schema for the request sent to LLM."""

    conversation: tuple[str, str] = Field(
        ..., description="Conversation for the request to the LLM"
    )  # noqa
    screenshot: bytes | None = Field(..., description="Main objective to be achieved")


class LLMTestStepPlanResponse(BaseModel):
    """Schema for the response received from LLM."""

    current_step_analysis: str
    screenshot_analysis: str
    previous_actions_analysis: str
    workers: list[WorkerConfig]
    sequence_type: SequenceType


class LLMTestStepFollowUpResponse(BaseModel):
    """Schema for the response received from LLM."""

    workers_analysis: str
    last_screenshot_analysis: str
    workers: list[WorkerConfig]
    sequence_type: SequenceType


class DataExtractionEntry(BaseModel):
    entry_type: str
    value: str


class LLMDataExtractionResponse(BaseModel):
    entries: list[DataExtractionEntry]


class LLMTestSequencePart(BaseModel):
    workers: list[WorkerConfig]
    sequence_type: SequenceType


class RecoverDecision(str, Enum):
    try_again = "try new plan"
    stop = "assign verdict"


class LLMTestStepRecoverResponse(BaseModel):
    """Schema for the response received from LLM."""

    workers_analysis: str
    recovery: str
    decision: RecoverDecision
    plan: LLMTestSequencePart = None
    # status: Status = None


class ClickCommand(BaseModel):
    name: Literal["click"]
    label: int


class GotoCommand(BaseModel):
    name: Literal["goto"]
    url: str


class FillCommand(BaseModel):
    name: Literal["fill"]
    label: int
    value: str


class SelectCommand(BaseModel):
    name: Literal["select"]
    label: int
    options: str


class ScrollCommand(BaseModel):
    name: Literal["scroll"]
    direction: Literal["up", "down"]


class FinishCommand(BaseModel):
    name: Literal["finish"]
    status: Status
    reason: str = None


Command = (
    ClickCommand
    | GotoCommand
    | FillCommand
    | SelectCommand
    | ScrollCommand
    | FinishCommand
)


class LLMActResponse(BaseModel):
    """Schema for the response received from LLM."""

    current_webpage_identification: str
    screenshot_analysis: str
    query_progress: str
    next_action: str
    command: Command

    def get_cot(self) -> str:
        data = self.model_dump_json(exclude={"command"})
        return str(data)


class CommandType(str, Enum):
    click = "click"
    goto = "goto"
    fill = "fill"
    select = "select"
    scroll = "scroll"
    finish = "finish"


class GoogleCommand(BaseModel):
    name: CommandType
    args: list[list[str]] = Field(..., description="the command args")


class LLMActResponseGoogle(BaseModel):
    """Schema for the response received from LLM."""

    current_webpage_identification: str
    screenshot_analysis: str
    query_progress: str
    next_action: str
    # command: GoogleCommand = Field(..., description="Command to perform on the web app")
    click: ClickCommand | None = None
    goto: GotoCommand | None = None
    fill: FillCommand | None = None
    select: SelectCommand | None = None
    scroll: ScrollCommand | None = None
    finish: FinishCommand | None = None


class LLMAssertResponse(BaseModel):
    """Schema for the response received from LLM."""

    page_description: str
    assertion_checking: AssertionChecking
    verdict: AssertionVerdict

    def get_cot(self) -> str:
        data = self.model_dump_json()
        return str(data)


def to_llm_act_response(response: LLMActResponseGoogle) -> LLMActResponse:
    """Converts LLMActResponseGoogle to LLMActResponse."""
    command: Command
    if response.command.name == "click":
        command = ClickCommand.model_validate(
            ast.literal_eval(response.command.model_dump_json())
        )
    elif response.command.name == "goto":
        command = GotoCommand.model_validate(
            ast.literal_eval(response.command.model_dump_json())
        )
    elif response.command.name == "fill":
        command = FillCommand.model_validate(
            ast.literal_eval(response.command.model_dump_json())
        )
        # case "goto":
        #     command = response.goto
        # case "fill":
        #     command = response.fill
        # case "select":
        #     command = response.select
        # case "scroll":
        #     command = response.scroll
        # case "finish":
        #     command = response.finish
    else:
        raise ValueError("No command found in LLMActResponseGoogle")

    return LLMActResponse(
        current_webpage_identification=response.current_webpage_identification,
        screenshot_analysis=response.screenshot_analysis,
        query_progress=response.query_progress,
        next_action=response.next_action,
        command=command,
    )
