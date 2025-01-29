import ast
import base64
from collections.abc import Iterable
import re
from typing import final

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
from VTAAS.schemas.verdict import WorkerResult
from openai import OpenAIError, AsyncOpenAI


from ..schemas.worker import Message, MessageRole, WorkerConfig, WorkerType
from ..schemas.llm import (
    LLMActResponse,
    LLMAssertResponse,
    LLMRequest,
    LLMTestStepPlanResponse,
)

# from ..schemas.worker_schemas import ActorWorker, AssertorWorker
from ..utils.logger import get_logger
from ..utils.config import load_config
import sys

logger = get_logger(__name__)


@final
class LLMClient:
    """Skeleton LLM client."""

    def __init__(self):
        # Load environment variables
        load_config()

        logger.info("Connection to OpenAI ...")

        try:
            # self.client = OpenAI()
            self.aclient = AsyncOpenAI()

        except OpenAIError as e:
            logger.fatal(e, exc_info=True)
            sys.exit(1)

    async def plan_for_step(self, request: LLMRequest) -> list[WorkerConfig]:
        """Get worker configurations from LLM."""
        try:
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": request.conversation[0],
                    },
                    {
                        "role": "user",
                        "content": request.conversation[1],
                    },
                ],
                response_format=LLMTestStepPlanResponse,
            )

            # logger.info(
            #     f"Received {response.choices[0].message.content} worker configurations from LLM"
            # )
            print(f"Model response:\n{response.choices[0].message.content}")

            # Parse and validate response
            llm_response = LLMTestStepPlanResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )

            logger.info(
                f"Received {len(llm_response.workers)} worker configurations from LLM"
            )
            return llm_response.workers

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    async def act(self, conversation: list[Message]) -> LLMActResponse:
        """Get worker configurations from LLM."""
        try:
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=self._to_openai_messages(conversation),
                response_format=LLMActResponse,
            )

            # logger.info(
            #     f"Received {response.choices[0].message.content} worker configurations from LLM"
            # )
            logger.debug(f"Act response:\n{response.choices[0].message.content}")
            if not response.choices[0].message.content:
                raise Exception("LLM response is empty")

            # Parse and validate response
            llm_response = LLMActResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )

            logger.info(f"Received command {llm_response.command.name} from Actor LLM")
            return llm_response

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    async def assert_(self, request: LLMRequest) -> LLMAssertResponse:
        """Get worker configurations from LLM."""
        try:
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": request.conversation[0],
                    },
                    {
                        "role": "user",
                        "content": request.conversation[1],
                    },
                ],
                response_format=LLMAssertResponse,
            )

            # logger.info(
            #     f"Received {response.choices[0].message.content} worker configurations from LLM"
            # )
            print(f"Assert response:\n{response.choices[0].message.content}")
            if not response.choices[0].message.content:
                logger.info("Assert LLM Response is empty")
                raise Exception("Assert LLM response is empty")

            # Parse and validate response
            llm_response = LLMAssertResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )

            logger.info(f"Received assertion {llm_response.verdict} from Actor LLM")
            return llm_response

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise

    def _extract_worker_sequence(self, response: str) -> list[WorkerConfig]:
        xml_pattern = r"<act_assert_sequence>(.*?)</act_assert_sequence>"
        match = re.search(xml_pattern, response, re.DOTALL)
        if match:
            workers: list[WorkerConfig] = []
            inner_content = match.group(1)
            for w in inner_content.splitlines():
                act_pattern = r"act\(\"(.*?)\"\)"
                match = re.search(act_pattern, w, re.DOTALL)
                if match:
                    workers.append(
                        WorkerConfig(type=WorkerType.ACTOR, query=match.group(1))
                    )
                    continue
                assert_pattern = r"assert\(\"(.*?)\"\)"
                match = re.search(assert_pattern, w, re.DOTALL)
                if match:
                    workers.append(
                        WorkerConfig(type=WorkerType.ASSERTOR, query=match.group(1))
                    )
            return workers
        return []

    async def get_step_verdict(self, request: LLMRequest) -> WorkerResult:
        """Get verdict for step case from the LLM. Used by Assertor Workers"""
        try:
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "system",
                        "content": "super system prompt",
                    },  # TODO: Put system prompt in assertor
                    {
                        "role": "user",
                        "content": f"{request.conversation}\nscreenshot: {request.screenshot}",
                    },
                ],
                response_format=WorkerResult,
            )

            # Parse and validate response
            llm_response: WorkerResult = WorkerResult.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )

            logger.info(f"Received status {llm_response.status}")
            return llm_response

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
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
                        base64_screenshot = base64.b64encode(msg.screenshot)
                        print(f"start of screenshot: {base64_screenshot[:50]}")
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
