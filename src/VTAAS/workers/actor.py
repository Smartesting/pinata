from typing import TypeGuard, final, override

from ..schemas.llm import (
    ClickCommand,
    Command,
    FillCommand,
    FinishCommand,
    GotoCommand,
    ScrollCommand,
    SelectCommand,
)
from ..schemas.verdict import ActorAction, ActorResult, WorkerResult
from ..utils.llm_client import LLMClient
from ..workers.browser import Browser
from ..schemas.worker import (
    ActorInput,
    Message,
    MessageRole,
    Worker,
    WorkerInput,
    WorkerType,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


@final
class Actor(Worker):
    """The Actor receives an ACT query and issues browser commands to perform the query"""

    def __init__(self, query: str, browser: Browser):
        super().__init__(query, browser)
        self.type = WorkerType.ACTOR
        self.llm_client = LLMClient()
        self.actions: list[ActorAction] = []
        self.query = query
        # self.priority = config.action_priority
        # self.can_modify = config.can_modify
        logger.info(f"Actor {self.id} initialized with query: {self.query}")

    @override
    async def process(self, input: WorkerInput) -> WorkerResult:
        """Actor execution loop"""
        if not self._is_actor_input(input):
            raise TypeError("Expected input of type ActorInput")
        await self.browser.mark_page()
        screenshot = await self.browser.screenshot()
        self._setup_conversation(input, screenshot)
        verdict: WorkerResult | None = None
        while verdict is None:
            response = await self.llm_client.act(self.conversation)
            command = response.command
            if command.name == "finish":
                logger.info(
                    f"Actor {self.id} Status {command.status}: {command.reason or 'No reason'}"
                )
                verdict = ActorResult(
                    status=command.status,
                    actions=self.actions,
                    explaination=command.reason,
                )
                continue
            self.conversation.append(
                Message(
                    role=MessageRole.Assistant,
                    content=response.model_dump_json(),
                )
            )
            action = self.command_to_str(command)
            outcome = await self.run_command(command)
            self.actions.append(ActorAction(action=action, outcome=outcome))
            await self.browser.mark_page()
            screenshot = await self.browser.screenshot()
            self.conversation.append(
                Message(role=MessageRole.User, content=outcome, screenshot=screenshot)
            )
        return verdict

    async def run_command(self, command: Command) -> str:
        match command:
            case ClickCommand(name="click"):
                return await self.browser.click(str(command.label))
            case GotoCommand(name="goto"):
                return await self.browser.goto(command.url)
            case FillCommand(name="fill"):
                return await self.browser.fill(str(command.label), command.value)
            case SelectCommand(name="select"):
                return await self.browser.select(str(command.label), command.options)
            case ScrollCommand(name="scroll"):
                return await self.browser.vertical_scroll(command.direction)
            case FinishCommand(name="finish"):
                return ""

    def command_to_str(self, command: Command) -> str:
        match command:
            case ClickCommand(name="click"):
                return f"click on label {command.label}"
            case GotoCommand(name="goto"):
                return f"goto {command.url}"
            case FillCommand(name="fill"):
                return f"fill {command.value} on label {command.label}"
            case SelectCommand(name="select"):
                return f"set option(s) {command.options} for label {command.label}"
            case ScrollCommand(name="scroll"):
                return f"scrolled {command.direction}"
            case FinishCommand(name="finish"):
                return ""

    @property
    def system_prompt(self) -> str:
        return "You are part of a multi-agent systems. Your role is to perform the task on a web application"

    def _setup_conversation(self, input: ActorInput, screenshot: bytes):
        self.conversation = [
            Message(role=MessageRole.System, content=self.system_prompt),
            Message(
                role=MessageRole.User,
                content=self._build_user_prompt(input),
                screenshot=screenshot,
            ),
        ]

    def _is_actor_input(self, input: WorkerInput) -> TypeGuard[ActorInput]:
        return isinstance(input, ActorInput)

    def _build_user_prompt(self, input: ActorInput) -> str:
        with open(
            "./src/VTAAS/workers/actor_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()

        current_step = input.test_step[0] + "; " + input.test_step[1]

        return prompt_template.format(
            test_case=input.test_case,
            current_step=current_step,
            history=input.history,
            query=self.query,
        )
