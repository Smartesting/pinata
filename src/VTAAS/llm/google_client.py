import ast
from typing import final, override
from google import genai
from google.genai import types

from VTAAS.llm.llm_client import LLMClient

from ..schemas.worker import Message, MessageRole
from ..schemas.llm import (
    LLMActResponse,
    LLMActResponseGoogle,
    LLMAssertResponse,
    LLMDataExtractionResponse,
    LLMTestStepFollowUpResponse,
    LLMTestStepPlanResponse,
    LLMTestStepRecoverResponse,
    to_llm_act_response,
)

from ..utils.logger import get_logger
from ..utils.config import load_config


@final
class GoogleLLMClient(LLMClient):
    """Communication with OpenAI"""

    def __init__(self, start_time: float):
        load_config()
        self.start_time = start_time
        self.logger = get_logger(__name__, self.start_time)
        self.client = genai.Client()

    @override
    async def plan_step(self, conversation: list[Message]) -> LLMTestStepPlanResponse:
        """Get list of act/assert workers from LLM."""
        try:
            self.logger.info(f"Init Plan Step Message:\n{conversation[-1].content}")
            response = self.client.models.generate_content(
                model="gemini-2.0-pro-exp-02-05",
                contents=self._to_google_messages(conversation),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LLMTestStepPlanResponse,
                ),
            )
            llm_response = LLMTestStepPlanResponse.model_validate(
                ast.literal_eval(response.text or "")
            )
            self.logger.info(
                f"Orchestrator Plan response:\n{llm_response.model_dump_json(indent=4)}"
            )
            self.logger.info(
                f"Received {len(llm_response.workers)} worker configurations from LLM"
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
            response = self.client.models.generate_content(
                model="gemini-2.0-pro-exp-02-05",
                contents=self._to_google_messages(conversation),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LLMTestStepFollowUpResponse,
                ),
            )
            llm_response = LLMTestStepFollowUpResponse.model_validate(
                ast.literal_eval(response.text or "")
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
            response = self.client.models.generate_content(
                model="gemini-2.0-pro-exp-02-05",
                contents=self._to_google_messages(conversation),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LLMTestStepRecoverResponse,
                ),
            )
            llm_response = LLMTestStepRecoverResponse.model_validate(
                ast.literal_eval(response.text or "")
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
            print(f"act json schema: {LLMActResponseGoogle.model_json_schema()}")
            response = self.client.models.generate_content(
                model="gemini-1.5-pro",
                contents=self._to_google_messages(conversation),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LLMActResponseGoogle,
                ),
            )
            if not response.text:
                raise Exception("LLM response is empty")
            self.logger.info(f"Received Actor response {response.text}")
            llm_response = LLMActResponseGoogle.model_validate(
                ast.literal_eval(response.text or "")
            )
            return to_llm_act_response(llm_response)

        except Exception as e:
            self.logger.error(f"Error in act call: {str(e)}")
            raise

    @override
    async def assert_(self, conversation: list[Message]) -> LLMAssertResponse:
        """Assertor call"""
        try:
            self.logger.info(f"Assertor User Message:\n{conversation[-1].content}")
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=self._to_google_messages(conversation),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LLMAssertResponse,
                ),
            )
            if not response.text:
                raise Exception("LLM response is empty")
            llm_response = LLMAssertResponse.model_validate(
                ast.literal_eval(response.text or "")
            )
            self.logger.info(
                f"Received Assertor response {llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            self.logger.error(f"Error in assert call: {str(e)}")
            raise

    @override
    async def step_postprocess(
        self, system: str, user: str, screenshots: list[bytes]
    ) -> LLMDataExtractionResponse:
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
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=self._to_google_messages(conversation),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LLMDataExtractionResponse,
                ),
            )
            resp_msg = response.text
            if not resp_msg:
                raise Exception("Synthesis response is empty")
            llm_response = LLMDataExtractionResponse.model_validate(
                ast.literal_eval(response.text or "")
            )

            self.logger.info(
                f"Received Synthesis response:\n{llm_response.model_dump_json(indent=4)}"
            )
            return llm_response

        except Exception as e:
            self.logger.error(f"Error in assert call: {str(e)}")
            raise

    def _to_google_messages(
        self, conversation: list[Message]
    ) -> list[types.ContentUnion]:
        messages: list[types.ContentUnion] = []
        for msg in conversation:
            match msg.role:
                case MessageRole.Assistant:
                    messages.append(
                        types.Content(
                            role="model", parts=[types.Part(text=msg.content)]
                        )
                    )
                case MessageRole.User:
                    content: list[types.Part] = [types.Part(text=msg.content)]
                    if msg.screenshot:
                        for screenshot in msg.screenshot:
                            content.append(
                                types.Part.from_bytes(
                                    data=screenshot,
                                    mime_type="image/png",
                                )
                            )
                    messages.append(types.Content(role="user", parts=content))
                case _:  # we dismiss system prompts with google, for now
                    continue
        return messages
