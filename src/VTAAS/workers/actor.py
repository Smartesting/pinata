from datetime import datetime
import os
from typing import TypeGuard, final, override

from VTAAS.llm.llm_client import LLMClient, LLMProviders
from VTAAS.llm.utils import create_llm_client
from VTAAS.utils.banner import add_banner

from ..schemas.llm import (
    ClickCommand,
    Command,
    FillCommand,
    FinishCommand,
    GotoCommand,
    ScrollCommand,
    SelectCommand,
)
from ..schemas.verdict import ActorAction, ActorResult, Status, WorkerResult
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

    def __init__(
        self,
        query: str,
        browser: Browser,
        llm_provider: LLMProviders,
        max_rounds: int = 4,
    ):
        super().__init__(query, browser)
        self.type = WorkerType.ACTOR
        self.llm_client: LLMClient = create_llm_client(llm_provider)
        self.actions: list[ActorAction] = []
        self.query = query
        self.max_rounds = max_rounds
        logger.info(f"Actor {self.id[:8]} initialized with query: {self.query}")

    @override
    async def process(self, input: WorkerInput) -> WorkerResult:
        """Actor execution loop"""
        if not self._is_actor_input(input):
            raise TypeError("Expected input of type ActorInput")
        await self.browser.mark_page()
        screenshot = await self.browser.screenshot()
        self._setup_conversation(input, screenshot)
        verdict: WorkerResult | None = None
        round = 0
        logger.info(f"Actor {self.id[:8]} processing query '{self.query}'")
        while verdict is None and round < self.max_rounds:
            round += 1
            response = await self.llm_client.act(self.conversation)
            command = response.command
            if command.name == "finish":
                logger.info(
                    f'Actor {self.id[:8]} ("{self.query}") is DONE: {command.status} - {command.reason or "No reason"}'
                )
                verdict = ActorResult(
                    query=self.query,
                    status=command.status,
                    actions=self.actions,
                    screenshot=self._add_banner(screenshot, f'act("{self.query}")'),
                    explaination=command.reason,
                )
                continue
            self.conversation.append(
                Message(
                    role=MessageRole.Assistant,
                    content=response.model_dump_json(),
                )
            )
            # action = self.command_to_str(command)
            outcome = f"Browser response:\n{await self.run_command(command)}"
            self.actions.append(
                ActorAction(action=outcome, chain_of_thought=response.get_cot())
            )
            await self.browser.mark_page()
            screenshot = await self.browser.screenshot()
            await self.browser.unmark_page()
            logger.info(outcome)
            outcome += f'\nIs the task "{self.query}" now complete?'
            self.conversation.append(
                Message(role=MessageRole.User, content=outcome, screenshot=[screenshot])
            )
        return verdict or ActorResult(
            query=self.query,
            status=Status.UNK,
            actions=self.actions,
            screenshot=self._add_banner(screenshot, f'act("{self.query}")'),
            explaination="stopped after 3 rounds",
        )

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

    @property
    def system_prompt(self) -> str:
        return "You are part of a multi-agent systems. Your role is to perform the provided query on a web application"

    def _setup_conversation(self, input: ActorInput, screenshot: bytes):
        self.conversation = [
            Message(role=MessageRole.System, content=self.system_prompt),
            Message(
                role=MessageRole.User,
                content=self._build_user_prompt(input),
                screenshot=[screenshot],
            ),
        ]
        logger.debug(f"User prompt:\n\n{self.conversation[1].content}")

    def _is_actor_input(self, input: WorkerInput) -> TypeGuard[ActorInput]:
        return isinstance(input, ActorInput)

    def _add_banner(self, screenshot: bytes, query: str) -> bytes:
        banner_screenshot = add_banner(screenshot, query)
        self._save_screenshot(banner_screenshot)
        return banner_screenshot

    def _save_screenshot(self, screenshot: bytes):
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshots/{self.id}_act_{timestamp}.png"
        with open(filename, "wb") as f:
            _ = f.write(screenshot)

    def _build_user_prompt(self, input: ActorInput) -> str:
        with open(
            "./src/VTAAS/workers/actor_prompt.txt", "r", encoding="utf-8"
        ) as prompt_file:
            prompt_template = prompt_file.read()

        # current_step = input.test_step[0] + "; " + input.test_step[1]

        return prompt_template.format(
            # test_case=input.test_case,
            # current_step=current_step,
            history=input.history,
            query=self.query,
        )
