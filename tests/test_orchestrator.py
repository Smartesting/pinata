from typing import cast
import pytest
from VTAAS.orchestrator import Orchestrator
from unittest.mock import Mock

from VTAAS.utils.llm_client import LLMClient


@pytest.fixture
def mock_llm_client(mocker) -> LLMClient:
    mocked_class = mocker.patch(
        "VTAAS.orchestrator.orchestrator.LLMClient", autospec=True
    )
    mock_instance: LLMClient = cast(LLMClient, mocked_class.return_value)

    mock_instance.get_worker_configs = Mock()
    mock_instance.get_step_verdict = Mock()
    # mock_instance.get_worker_configs.return_value = [...]
    # mock_instance.get_step_verdict.return_value = ...

    return mock_instance


@pytest.fixture
def orchestrator(mock_llm_client: LLMClient) -> Orchestrator:
    return Orchestrator()


@pytest.mark.asyncio
async def test_main_prompt(orchestrator: Orchestrator):
    """Test main prompt builds itself"""
    prompt = orchestrator._get_user_prompt(1)
    test_case = "blablabla"
    action = "Login as superuser/trial"
    assertion = "Logged in as admin"
    test_step = f"1. action: {action}, assertion: {assertion}"
    assert f"<test_case>\n{test_case}\n</test_case>" in prompt
    assert f"<current_step>\n{test_step}\n</current_step>" in prompt
