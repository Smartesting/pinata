import ast
import base64
from collections.abc import Iterable
import json
from typing import final, override

from anthropic import AsyncAnthropic
from anthropic.types import TextBlock
from anthropic.types.image_block_param import ImageBlockParam, Source
from anthropic.types.message_param import MessageParam
from anthropic.types.text_block_param import TextBlockParam
from pydantic import BaseModel

from VTAAS.llm.llm_client import LLMClient


from ..schemas.worker import Message, MessageRole
from ..schemas.llm import (
    LLMActResponse,
    LLMAssertResponse,
    LLMSynthesisResponse,
    LLMTestStepFollowUpResponse,
    LLMTestStepPlanResponse,
    LLMTestStepRecoverResponse,
)

from ..utils.logger import get_logger
from ..utils.config import load_config
import sys


@final
class AnthropicLLMClient(LLMClient):
    """Communication with OpenAI"""

    def __init__(self, start_time: float):
        load_config()
        self.start_time = start_time
        self.logger = get_logger(__name__, self.start_time)
        try:
            self.aclient = AsyncAnthropic(max_retries=4)
        except Exception as e:
            self.logger.fatal(e, exc_info=True)
            sys.exit(1)

    @override
    async def plan_step(self, conversation: list[Message]) -> LLMTestStepPlanResponse:
        """Get list of act/assert workers from LLM."""
        try:
            self.logger.info(f"Init Plan Step Message:\n{conversation[-1].content}")
            expected_format = AnthropicLLMClient.generate_prompt_from_pydantic(
                LLMTestStepPlanResponse
            )
            # preshot_assistant = Message(
            #     role=MessageRole.Assistant,
            #     content=AnthropicLLMClient.build_json_start(LLMTestStepPlanResponse),
            # )
            # conversation.append(preshot_assistant)
            response = await self.aclient.messages.create(
                max_tokens=1000,
                model="claude-3-5-sonnet-latest",
                messages=AnthropicLLMClient.to_anthropic_messages(
                    conversation, expected_format
                ),
            )
            if len(response.content) == 0:
                raise ValueError("PLAN - anthropic response is empty")
            outcome = response.content[0]
            if not isinstance(outcome, TextBlock):
                raise ValueError("PLAN - anthropic response is not text")
            llm_response = LLMTestStepPlanResponse.model_validate(
                ast.literal_eval(outcome.text or "")
            )
            self.logger.info(
                f"Orchestrator Plan response:\n{llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            self.logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    @override
    async def followup_step(
        self, conversation: list[Message]
    ) -> LLMTestStepFollowUpResponse:
        """Update list of act/assert workers from LLM."""
        try:
            self.logger.info(f"FollowUp Plan Step Message:\n{conversation[-1].content}")
            expected_format = AnthropicLLMClient.generate_prompt_from_pydantic(
                LLMTestStepFollowUpResponse
            )
            response = await self.aclient.messages.create(
                max_tokens=1000,
                model="claude-3-5-sonnet-latest",
                messages=self.to_anthropic_messages(conversation, expected_format),
            )
            if len(response.content) == 0:
                raise ValueError("FOLLOWUP - anthropic response is empty")
            outcome = response.content[0]
            if not isinstance(outcome, TextBlock):
                raise ValueError("FOLLOWUP - anthropic response is not text")
            llm_response = LLMTestStepFollowUpResponse.model_validate(
                ast.literal_eval(outcome.text or "")
            )
            self.logger.info(
                f"Orchestrator Follow-Up response:\n{llm_response.model_dump_json(indent=4)}"
            )
            self.logger.info(
                f"Follow-Up: Received {len(llm_response.workers)} new worker configurations from LLM"
            )
            return llm_response

        except Exception as e:
            self.logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    @override
    async def recover_step(
        self, conversation: list[Message]
    ) -> LLMTestStepRecoverResponse:
        """Update list of act/assert workers from LLM."""
        try:
            self.logger.info(f"Recover Step Message:\n{conversation[-1].content}")
            expected_format = AnthropicLLMClient.generate_prompt_from_pydantic(
                LLMTestStepRecoverResponse
            )
            response = await self.aclient.messages.create(
                max_tokens=1000,
                model="claude-3-5-sonnet-latest",
                messages=self.to_anthropic_messages(conversation, expected_format),
            )
            if len(response.content) == 0:
                raise ValueError("RECOVER - anthropic response is empty")
            outcome = response.content[0]
            if not isinstance(outcome, TextBlock):
                raise ValueError("RECOVER - anthropic response is not text")
            llm_response = LLMTestStepRecoverResponse.model_validate(
                ast.literal_eval(outcome.text or "")
            )
            self.logger.info(
                f"Orchestrator Recover response:\n{llm_response.model_dump_json(indent=4)}"
            )
            if llm_response.plan:
                self.logger.info(
                    f"[Recover] Received {len(llm_response.plan.workers)} worker configurations from LLM"
                )
            else:
                self.logger.info("[Recover] Test step is considered FAIL")

            return llm_response

        except Exception as e:
            self.logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    @override
    async def act(self, conversation: list[Message]) -> LLMActResponse:
        """Actor call"""
        try:
            self.logger.info(f"Actor User Message:\n{conversation[-1].content}")
            expected_format = AnthropicLLMClient.generate_prompt_from_pydantic(
                LLMActResponse
            )
            response = await self.aclient.messages.create(
                max_tokens=1000,
                model="claude-3-5-sonnet-latest",
                messages=self.to_anthropic_messages(conversation, expected_format),
                # response_format=LLMActResponse,
            )
            if len(response.content) == 0:
                raise ValueError("ACT - anthropic response is empty")
            outcome = response.content[0]
            if not isinstance(outcome, TextBlock):
                raise ValueError("ACT - anthropic response is not text")
            llm_response = LLMActResponse.model_validate(
                ast.literal_eval(outcome.text or "")
            )
            self.logger.info(
                f"Received Actor response {llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            self.logger.error(f"Error in act call: {str(e)}")
            raise

    @override
    async def assert_(self, conversation: list[Message]) -> LLMAssertResponse:
        """Assertor call"""
        try:
            self.logger.info(f"Assertor User Message:\n{conversation[-1].content}")
            expected_format = AnthropicLLMClient.generate_prompt_from_pydantic(
                LLMAssertResponse
            )
            response = await self.aclient.messages.create(
                max_tokens=1000,
                model="gpt-4o-mini",
                messages=self.to_anthropic_messages(conversation, expected_format),
                # response_format=LLMAssertResponse,
            )
            if len(response.content) == 0:
                raise ValueError("ASSERT - anthropic response is empty")
            outcome = response.content[0]
            if not isinstance(outcome, TextBlock):
                raise ValueError("ASSERT - anthropic response is not text")
            llm_response = LLMAssertResponse.model_validate(
                ast.literal_eval(outcome.text or "")
            )
            self.logger.info(
                f"Received Assertor response {llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            self.logger.error(f"Error in assert call: {str(e)}")
            raise

    @override
    async def step_synthesis(
        self, system: str, user: str, screenshots: list[bytes]
    ) -> LLMSynthesisResponse:
        """Synthesis call"""
        try:
            conversation: list[Message] = [
                Message(role=MessageRole.System, content=system),
                Message(
                    role=MessageRole.User,
                    content=user,
                    screenshot=screenshots,
                ),
            ]
            expected_format = AnthropicLLMClient.generate_prompt_from_pydantic(
                LLMSynthesisResponse
            )
            response = await self.aclient.messages.create(
                max_tokens=1024,
                model="claude-3-5-sonnet-latest",
                messages=self.to_anthropic_messages(conversation, expected_format),
            )
            if len(response.content) == 0:
                raise ValueError("SYNTHESIS - anthropic response is empty")
            outcome = response.content[0]
            if not isinstance(outcome, TextBlock):
                raise ValueError("SYNTHESIS - anthropic response is not text")
            llm_response = LLMSynthesisResponse.model_validate(
                ast.literal_eval(outcome.text or "")
            )

            self.logger.info(
                f"Received Synthesis response:\n{llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            self.logger.error(f"Error in assert call: {str(e)}")
            raise

    @staticmethod
    def to_anthropic_messages(
        conversation: list[Message], prompt_json_format: str
    ) -> Iterable[MessageParam]:
        messages: Iterable[MessageParam] = []
        conv_length = len(conversation)
        for idx, msg in enumerate(conversation):
            match msg.role:
                case MessageRole.System:
                    continue
                case MessageRole.Assistant:
                    messages.append(MessageParam(role="assistant", content=msg.content))
                case MessageRole.User:
                    content: Iterable[TextBlockParam | ImageBlockParam] = []
                    format_suffix = prompt_json_format if idx == conv_length - 1 else ""
                    content.append(
                        TextBlockParam(type="text", text=msg.content + format_suffix)
                    )
                    if msg.screenshot:
                        for screenshot in msg.screenshot:
                            base64_screenshot = str(
                                base64.b64encode(screenshot), "utf-8"
                            )
                            image = Source(
                                media_type="image/png",
                                data=base64_screenshot,
                                type="base64",
                            )
                            content.append(ImageBlockParam(source=image, type="image"))
                    messages.append(MessageParam(content=content, role="user"))
        return messages

    @staticmethod
    def generate_prompt_from_pydantic(model: type[BaseModel]) -> str:
        """
        Anthropic does not support structured outputs. Let's ask the model to adhere to the format in the prompt
        """
        schema = model.model_json_schema()

        prompt = (
            "Your response must be a json.loads parsable JSON object, following this JSON schema:\n\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```"
        )

        return prompt

    @staticmethod
    def build_json_start(model: type[BaseModel], indent: int = 0) -> str:
        """
        Recursively builds a JSON string up to the first unknown value.
        """
        properties: dict = model.model_json_schema()["properties"]
        json_parts = ["{"]
        first = True
        for key, value in properties.items():
            if not first:
                json_parts.append(",")
            first = False
            json_parts.append("\n" + " " * (indent + 2) + f'"{key}": ')

            if value["type"] == "object":
                json_parts.append(
                    AnthropicLLMClient.build_json_start(value["properties"], indent + 2)
                )
            else:
                json_parts.append("")
                break

        json_parts.append("\n" + " " * indent + "}")
        return "".join(json_parts)

    @staticmethod
    def extract_json(response: str) -> str:
        json_start = response.index("{")
        json_end = response.rfind("}")
        return response[json_start : json_end + 1]
