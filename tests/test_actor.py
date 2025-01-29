from typing import cast
from playwright.async_api import async_playwright
import pytest
from pytest_mock import MockerFixture
from unittest.mock import Mock

from VTAAS.data.testcase import TestCaseCollection
from VTAAS.schemas.verdict import Status
from VTAAS.schemas.worker import ActorInput
from VTAAS.utils.llm_client import LLMClient
from VTAAS.workers.actor import Actor
from VTAAS.workers.browser import Browser

MOCKED_QUERY = "This is a mock query"


@pytest.fixture
def mock_llm_client(mocker: MockerFixture) -> LLMClient:
    mocked_class = mocker.patch("VTAAS.workers.actor.LLMClient", autospec=True)
    mock_instance: LLMClient = cast(LLMClient, mocked_class.return_value)

    mock_instance.plan_for_step = Mock()
    mock_instance.get_step_verdict = Mock()
    # mock_instance.get_worker_configs.return_value = [...]
    # mock_instance.get_step_verdict.return_value = ...

    return mock_instance


@pytest.fixture
def mock_browser(mocker: MockerFixture) -> Browser:
    mocked_class = mocker.patch("VTAAS.workers.actor.Browser", autospec=True)
    mock_instance: Browser = cast(Browser, mocked_class.return_value)

    mock_instance.goto = Mock()
    mock_instance.click = Mock()
    mock_instance.fill = Mock()
    mock_instance.select = Mock()
    mock_instance.vertical_scroll = Mock()
    # mock_instance.get_worker_configs.return_value = [...]
    # mock_instance.get_step_verdict.return_value = ...

    return mock_instance


@pytest.fixture
def mock_query() -> str:
    return MOCKED_QUERY


@pytest.fixture
def mock_actor_input() -> ActorInput:
    return ActorInput(
        test_case="TC-1-P: Login & Logout\n1. login\n2.logout",
        test_step=("1. login", ""),
        history="filled 'user' in username field",
    )


@pytest.fixture
def empty_actor(mock_query: str, mock_browser: Browser) -> Actor:
    return Actor(mock_query, mock_browser)


@pytest.mark.asyncio
async def test_main_prompt(empty_actor: Actor, mock_actor_input: ActorInput):
    """Test main prompt builds itself"""
    prompt = empty_actor._build_user_prompt(mock_actor_input)
    print(prompt)
    current_step = mock_actor_input.test_step[0] + "; " + mock_actor_input.test_step[1]
    assert f"<test_case>\n{mock_actor_input.test_case}\n</test_case>" in prompt
    assert f"<current_step>\n{current_step}\n</current_step>" in prompt
    assert (
        f"<previous_actions>\n{mock_actor_input.history}\n</previous_actions>" in prompt
    )
    assert f"<act_query>\n{MOCKED_QUERY}\n</act_query>" in prompt


@pytest.mark.asyncio
async def test_conversation(empty_actor: Actor, mock_actor_input: ActorInput):
    """Test main prompt builds itself"""
    empty_actor._setup_conversation(mock_actor_input, b"")
    print(empty_actor.conversation)
    assert False


@pytest.mark.asyncio
@pytest.mark.llm
async def test_integ():
    url = "http://www.vtaas-benchmark.com:7770/"
    test_collection = TestCaseCollection("data/OneStop_Passing.csv", url)
    test_case = test_collection.get_test_case_by_id("1")
    test_step = test_case.get_step(2)
    query = "click on the 'Sign in' link"
    actor_input = ActorInput(
        test_case=str(test_case), test_step=test_step, history=None
    )
    async with async_playwright() as p:
        browser = await Browser.create(id="actor_browser", headless=False, playwright=p)
        _ = await browser.goto(url)
        actor = Actor(query, browser)
        verdict = await actor.process(actor_input)
        print(verdict)
        assert verdict.status == Status.PASS
