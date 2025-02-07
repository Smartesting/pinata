from typing import cast
from openai import AsyncOpenAI
import pytest

from VTAAS.schemas.llm import LLMRequest
from VTAAS.utils.config import load_config
from VTAAS.llm.openai_client import OpenAILLMClient


@pytest.mark.asyncio
async def test_plannif(empty_llm_client: OpenAILLMClient):
    """Test main prompt builds itself"""
    load_config()
    request = LLMRequest(
        conversation=("You are the best tester", "fill in the blanks"), screenshot=b""
    )
    plan = await empty_llm_client.plan_step(request)
    print(plan)


@pytest.fixture
def mock_openai(mocker) -> AsyncOpenAI:
    mocked_class = mocker.patch("VTAAS.llm.openai_client.AsyncOpenAI", autospec=True)
    mock_instance: AsyncOpenAI = cast(AsyncOpenAI, mocked_class.return_value)
    return mock_instance


@pytest.fixture
def empty_llm_client(mock_openai: AsyncOpenAI) -> OpenAILLMClient:
    return OpenAILLMClient()
