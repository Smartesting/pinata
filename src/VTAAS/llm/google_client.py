import ast
import logging
from typing import final, override
from google import genai
from google.genai import types

from VTAAS.llm.llm_client import LLMClient

from ..schemas.worker import Message, MessageRole
from ..schemas.llm import (
    LLMActGoogleResponse,
    LLMActResponse,
    LLMAssertResponse,
    LLMDataExtractionResponse,
    LLMTestStepFollowUpResponse,
    LLMTestStepPlanResponse,
    LLMTestStepRecoverResponse,
)

from ..utils.logger import get_logger
from ..utils.config import load_config


@final
class GoogleLLMClient(LLMClient):
    """Communication with OpenAI"""

    def __init__(self, start_time: float):
        load_config()
        self.start_time = start_time
        self.max_tries = 3
        self.logger = get_logger("Google LLM Client", self.start_time)
        self.logger.setLevel(logging.DEBUG)
        self.client = genai.Client()

    @override
    async def plan_step(self, conversation: list[Message]) -> LLMTestStepPlanResponse:
        """Get list of act/assert workers from LLM."""
        attempts = 1
        while attempts <= self.max_tries:
            try:
                self.logger.info(f"Init Plan Step Message:\n{conversation[-1].content}")
                response = self.client.models.generate_content(
                    model="gemini-2.0-pro-exp-02-05",
                    contents=self._to_google_messages(conversation),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMTestStepPlanResponse,
                        temperature=0,
                        seed=192837465,
                    ),
                )
            except Exception as e:
                self.logger.error(f"Error #{attempts} in plan step call: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue

            try:
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
                self.logger.error(f"Error #{attempts} in plan step parsing: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
        raise Exception("could not send Step planning request")

    @override
    async def followup_step(
        self, conversation: list[Message]
    ) -> LLMTestStepFollowUpResponse:
        """Update list of act/assert workers from LLM."""
        attempts = 1
        while attempts <= self.max_tries:
            try:
                self.logger.info(
                    f"FollowUp Plan Step Message:\n{conversation[-1].content}"
                )
                response = self.client.models.generate_content(
                    model="gemini-2.0-pro-exp-02-05",
                    contents=self._to_google_messages(conversation),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMTestStepFollowUpResponse,
                        temperature=0,
                        seed=192837465,
                    ),
                )
            except Exception as e:
                self.logger.error(f"Error #{attempts} in plan followup call: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
            try:
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
                self.logger.error(
                    f"Error #{attempts} in plan followup parsing: {str(e)}"
                )
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
        raise Exception("could not send step planning followup request")

    @override
    async def recover_step(
        self, conversation: list[Message]
    ) -> LLMTestStepRecoverResponse:
        """Update list of act/assert workers from LLM."""
        attempts = 1
        while attempts <= self.max_tries:
            try:
                self.logger.info(f"Recover Step Message:\n{conversation[-1].content}")
                response = self.client.models.generate_content(
                    model="gemini-2.0-pro-exp-02-05",
                    contents=self._to_google_messages(conversation),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMTestStepRecoverResponse,
                        temperature=0,
                        seed=192837465,
                    ),
                )
            except Exception as e:
                self.logger.error(f"Error #{attempts} in plan recover call: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
            try:
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
                self.logger.error(
                    f"Error #{attempts} in plan recover parsing: {str(e)}"
                )
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
        raise Exception("could not send Step planning recover request")

    @override
    async def act(self, conversation: list[Message]) -> LLMActResponse:
        """Actor call"""
        attempts = 1
        while attempts <= self.max_tries:
            try:
                # self.logger.debug(f"Actor User Message:\n{conversation[-1].content}")
                response = self.client.models.generate_content(
                    model="gemini-2.0-pro-exp-02-05",
                    contents=self._to_google_messages(conversation),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMActGoogleResponse,
                        temperature=0,
                        seed=192837465,
                    ),
                )
            except Exception as e:
                self.logger.error(f"Error #{attempts} in act call: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
            try:
                if not response.text:
                    raise Exception("LLM response is empty")
                self.logger.debug(f"Received Actor raw response:\n{response.text}")
                llm_response = LLMActResponse.model_validate(
                    ast.literal_eval(response.text or "")
                )
                self.logger.info(
                    f"Actor response:\n{llm_response.model_dump_json(indent=4)}"
                )
                return llm_response

            except Exception as e:
                self.logger.error(f"Error #{attempts} in act parsing: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
        raise Exception("could not send Act request")

    @override
    async def assert_(self, conversation: list[Message]) -> LLMAssertResponse:
        """Assertor call"""
        attempts = 1
        while attempts <= self.max_tries:
            try:
                self.logger.info(f"Assertor User Message:\n{conversation[-1].content}")
                response = self.client.models.generate_content(
                    model="gemini-2.0-pro-exp-02-05",
                    contents=self._to_google_messages(conversation),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMAssertResponse,
                        temperature=0,
                        seed=192837465,
                    ),
                )
            except Exception as e:
                self.logger.error(f"Error #{attempts} in assert call: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
            try:
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
                self.logger.error(f"Error #{attempts} in assert parsing: {str(e)}")
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
        raise Exception("could not send Assert request")

    @override
    async def step_postprocess(
        self, system: str, user: str, screenshots: list[bytes]
    ) -> LLMDataExtractionResponse:
        """Data Extraction call"""
        attempts = 1
        while attempts <= self.max_tries:
            conversation: list[Message] = [
                Message(role=MessageRole.System, content=system),
                Message(
                    role=MessageRole.User,
                    content=user,
                    screenshot=screenshots,
                ),
            ]
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.0-pro-exp-02-05",
                    contents=self._to_google_messages(conversation),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMDataExtractionResponse,
                        temperature=0,
                        seed=192837465,
                    ),
                )
            except Exception as e:
                self.logger.error(
                    f"Error #{attempts} in data extraction call: {str(e)}"
                )
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
            try:
                resp_msg = response.text
                if not resp_msg:
                    raise Exception("Data extraction response is empty")
                llm_response = LLMDataExtractionResponse.model_validate(
                    ast.literal_eval(response.text or "")
                )

                self.logger.info(
                    f"Received Data Extraction response:\n{llm_response.model_dump_json(indent=4)}"
                )
                return llm_response

            except Exception as e:
                self.logger.error(
                    f"Error #{attempts} in data extraction parsing: {str(e)}"
                )
                if attempts >= self.max_tries:
                    raise
                attempts += 1
                continue
        raise Exception("could not send Data extraction request")

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
