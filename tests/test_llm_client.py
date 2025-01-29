from typing import cast
from openai import AsyncOpenAI
import pytest

from VTAAS.schemas.llm import LLMRequest
from VTAAS.utils.config import load_config
from VTAAS.utils.llm_client import LLMClient


@pytest.mark.asyncio
async def test_plannif():
    """Test main prompt builds itself"""
    load_config()
    llm_client = LLMClient()
    request = LLMRequest(
        conversation=("You are the best tester", "fill in the blanks"), screenshot=b""
    )
    plan = llm_client.plan_for_step(request)
    print(plan)


@pytest.fixture
def mock_openai(mocker) -> AsyncOpenAI:
    mocked_class = mocker.patch("VTAAS.utils.llm_client.AsyncOpenAI", autospec=True)
    mock_instance: AsyncOpenAI = cast(AsyncOpenAI, mocked_class.return_value)
    return mock_instance


@pytest.fixture
def empty_llm_client(mock_openai: AsyncOpenAI) -> LLMClient:
    return LLMClient()


@pytest.mark.asyncio
async def test_regex(empty_llm_client: LLMClient):
    """Test main prompt builds itself"""
    response = """
Here is my list
<act_assert_sequence>
act("this")
assert("that")
</act_assert_sequence>
Now do it!
    """
    print(empty_llm_client._extract_worker_sequence(response))
