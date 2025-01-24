from typing import cast
from openai import AsyncOpenAI
import pytest

from VTAAS.utils.llm_client import LLMClient


@pytest.fixture
def mock_openai(mocker) -> AsyncOpenAI:
    mocked_class = mocker.patch("VTAAS.utils.llm_client.AsyncOpenAI", autospec=True)
    mock_instance: AsyncOpenAI = cast(AsyncOpenAI, mocked_class.return_value)
    return mock_instance


@pytest.fixture
def llm_client(mock_openai: AsyncOpenAI) -> LLMClient:
    return LLMClient()


@pytest.mark.asyncio
async def test_regex(llm_client: LLMClient):
    """Test main prompt builds itself"""
    response = """
Here is my list
<act_assert_sequence>
act("this")
assert("that")
</act_assert_sequence>
Now do it!
    """
    print(llm_client._extract_worker_sequence(response))
