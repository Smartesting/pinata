import ast
import base64
from collections.abc import Iterable
from typing import final, override

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL
from openai import OpenAIError, AsyncOpenAI

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

logger = get_logger(__name__)


@final
class OpenAILLMClient(LLMClient):
    """Communication with OpenAI"""

    def __init__(self):
        load_config()
        try:
            self.aclient = AsyncOpenAI()
        except OpenAIError as e:
            logger.fatal(e, exc_info=True)
            sys.exit(1)

    @override
    async def plan_step(self, conversation: list[Message]) -> LLMTestStepPlanResponse:
        """Get list of act/assert workers from LLM."""
        try:
            logger.info(f"Init Plan Step Message:\n{conversation[-1].content}")
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-2024-11-20",
                messages=self._to_openai_messages(conversation),
                response_format=LLMTestStepPlanResponse,
            )
            logger.info(f"Model Plan response:\n{response.choices[0].message.content}")
            llm_response = LLMTestStepPlanResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )
            logger.info(
                f"Orchestrator Plan response:\n{llm_response.model_dump_json(indent=4)}"
            )
            logger.info(
                f"Received {len(llm_response.workers)} worker configurations from LLM"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    @override
    async def followup_step(
        self, conversation: list[Message]
    ) -> LLMTestStepFollowUpResponse:
        """Update list of act/assert workers from LLM."""
        try:
            logger.info(f"FollowUp Plan Step Message:\n{conversation[-1].content}")
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-2024-11-20",
                messages=self._to_openai_messages(conversation),
                response_format=LLMTestStepFollowUpResponse,
            )
            llm_response = LLMTestStepFollowUpResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )
            logger.info(
                f"Orchestrator Follow-Up response:\n{llm_response.model_dump_json(indent=4)}"
            )
            logger.info(
                f"Follow-Up: Received {len(llm_response.workers)} new worker configurations from LLM"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    @override
    async def recover_step(
        self, conversation: list[Message]
    ) -> LLMTestStepRecoverResponse:
        """Update list of act/assert workers from LLM."""
        try:
            logger.info(f"Recover Step Message:\n{conversation[-1].content}")
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-2024-11-20",
                messages=self._to_openai_messages(conversation),
                response_format=LLMTestStepRecoverResponse,
            )
            llm_response = LLMTestStepRecoverResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )
            logger.info(
                f"Orchestrator Recover response:\n{llm_response.model_dump_json(indent=4)}"
            )
            if llm_response.plan:
                logger.info(
                    f"[Recover] Received {len(llm_response.plan.workers)} worker configurations from LLM"
                )
            else:
                logger.info("[Recover] Test step is considered FAIL")

            return llm_response

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    @override
    async def act(self, conversation: list[Message]) -> LLMActResponse:
        """Actor call"""
        try:
            logger.info(f"Actor User Message:\n{conversation[-1].content}")
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-2024-11-20",
                messages=self._to_openai_messages(conversation),
                response_format=LLMActResponse,
            )
            if not response.choices[0].message.content:
                raise Exception("LLM response is empty")
            llm_response = LLMActResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )
            logger.info(
                f"Received Actor response {llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error in act call: {str(e)}")
            raise

    @override
    async def assert_(self, conversation: list[Message]) -> LLMAssertResponse:
        """Assertor call"""
        try:
            logger.info(f"Assertor User Message:\n{conversation[-1].content}")
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=self._to_openai_messages(conversation),
                response_format=LLMAssertResponse,
            )
            if not response.choices[0].message.content:
                raise Exception("LLM response is empty")
            llm_response = LLMAssertResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )
            logger.info(
                f"Received Assertor response {llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error in assert call: {str(e)}")
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
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=self._to_openai_messages(conversation),
                response_format=LLMSynthesisResponse,
            )
            resp_msg = response.choices[0].message.content
            if not resp_msg:
                raise Exception("Synthesis response is empty")
            llm_response = LLMSynthesisResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )

            logger.info(
                f"Received Synthesis response:\n{llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error in assert call: {str(e)}")
            raise

    def _to_openai_messages(
        self, conversation: list[Message]
    ) -> Iterable[ChatCompletionMessageParam]:
        messages: Iterable[ChatCompletionMessageParam] = []
        for msg in conversation:
            match msg.role:
                case MessageRole.System:
                    messages.append(
                        ChatCompletionSystemMessageParam(
                            role="system", content=msg.content
                        )
                    )
                case MessageRole.Assistant:
                    messages.append(
                        ChatCompletionAssistantMessageParam(
                            role="assistant", content=msg.content
                        )
                    )
                case MessageRole.User:
                    content: Iterable[ChatCompletionContentPartParam] = []
                    content.append(
                        ChatCompletionContentPartTextParam(
                            type="text", text=msg.content
                        )
                    )
                    if msg.screenshot:
                        for screenshot in msg.screenshot:
                            base64_screenshot = str(
                                base64.b64encode(screenshot), "utf-8"
                            )
                            image = ImageURL(
                                url=f"data:image/png;base64,{base64_screenshot}",
                                detail="high",
                            )
                            content.append(
                                ChatCompletionContentPartImageParam(
                                    image_url=image, type="image_url"
                                )
                            )
                    messages.append(
                        ChatCompletionUserMessageParam(content=content, role="user")
                    )
        return messages
