import ast
from openai import OpenAIError, AsyncOpenAI

from ..schemas.worker_schemas import BaseWorker
from ..schemas.llm_schemas import LLMWorkerRequest, LLMWorkerResponse

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

    async def get_worker_configs(self, request: LLMWorkerRequest) -> list[BaseWorker]:
        """Get worker configurations from LLM."""
        try:
            response = await self.aclient.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "super system prompt",
                    },  # TODO: Put system prompt in orchestrator
                    {
                        "role": "user",
                        "content": f"Context: {request.context}\nObjective: {request.objective}",
                    },
                ],
                response_format=LLMWorkerResponse,
            )

            # logger.info(
            #     f"Received {response.choices[0].message.content} worker configurations from LLM"
            # )

            # Parse and validate response
            llm_response = LLMWorkerResponse.model_validate(
                ast.literal_eval(response.choices[0].message.content)
            )

            logger.info(
                f"Received {len(llm_response.workers)} worker configurations from LLM"
            )
            return llm_response.workers

        except Exception as e:
            logger.error(f"Error getting worker configurations: {str(e)}")
            raise
