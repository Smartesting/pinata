import ast
import re
from VTAAS.schemas.verdict import WorkerVerdict
from openai import OpenAIError, AsyncOpenAI


from ..schemas.worker import Worker, WorkerConfig, WorkerType
from ..schemas.llm import LLMRequest, LLMWorkerResponse

# from ..schemas.worker_schemas import ActorWorker, ObserverWorker
from ..utils.logger import get_logger
from ..utils.config import load_config
import sys

logger = get_logger(__name__)


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
                        "content": request.prompt[0],
                    },
                    {
                        "role": "user",
                        "content": request.prompt[1],
                    },
                ],
                response_format=LLMWorkerResponse,
            )

            # logger.info(
            #     f"Received {response.choices[0].message.content} worker configurations from LLM"
            # )
            print(f"Model response:\n{response.choices[0].message.content}")

            # Parse and validate response
            llm_response = LLMWorkerResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )

            logger.info(
                f"Received {len(llm_response.workers)} worker configurations from LLM"
            )
            return llm_response.workers

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

    async def get_step_verdict(self, request: LLMRequest) -> WorkerVerdict:
        """Get verdict for step case from the LLM. Used by Observer Workers"""
        try:
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "system",
                        "content": "super system prompt",
                    },  # TODO: Put system prompt in observer
                    {
                        "role": "user",
                        "content": f"{request.prompt}\nscreenshot: {request.screenshot}",
                    },
                ],
                response_format=WorkerVerdict,
            )

            # Parse and validate response
            llm_response: WorkerVerdict = WorkerVerdict.model_validate(
                ast.literal_eval(response.choices[0].message.content or "")
            )

            logger.info(f"Received status {llm_response.status}")
            return llm_response

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise
