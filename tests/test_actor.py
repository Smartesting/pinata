from collections.abc import Generator
import logging
from typing import cast
from playwright.async_api import async_playwright
import pytest
from unittest.mock import AsyncMock, patch

from VTAAS.data.testcase import TestCaseCollection
from VTAAS.schemas.llm import (
    ClickCommand,
    FillCommand,
    FinishCommand,
    LLMActResponse,
)
from VTAAS.schemas.verdict import ActorResult, Status, WorkerResult
from VTAAS.schemas.worker import ActorInput, MessageRole
from VTAAS.utils.llm_client import LLMClient
from VTAAS.workers.actor import Actor
from VTAAS.workers.browser import Browser

MOCKED_QUERY = "This is a mock query"


def llm_act_response_generator() -> Generator[LLMActResponse, None, None]:
    responses = [
        LLMActResponse(
            current_webpage_identification="Home Page",
            screenshot_analysis="We see a login button at the top right-end corner, labelled '2'",
            query_progress="N/A",
            next_action="Click login button labelled '2'",
            command=ClickCommand(name="click", label=2),
        ),
        LLMActResponse(
            current_webpage_identification="Login page",
            screenshot_analysis="There's a single username field labelled '3'",
            query_progress="not yet",
            next_action="fill 'hello_AI' in username field labelled '3'",
            command=FillCommand(name="fill", label=3, value="hello_AI"),
        ),
        LLMActResponse(
            current_webpage_identification="Dashboard",
            screenshot_analysis="It appears the login was successful, a 'Welcome hello_AI' message is visible",
            query_progress="The query is complete",
            next_action="finish",
            command=FinishCommand(
                name="finish", status=Status.PASS, reason="Logged in as hello_AI"
            ),
        ),
    ]
    for response in responses:
        yield response


@pytest.fixture
def mock_llm_client() -> LLMClient:
    mock_instance: LLMClient = AsyncMock(spec=LLMClient)
    response_generator = llm_act_response_generator()
    mock_instance.act = AsyncMock(side_effect=lambda _: next(response_generator))
    return mock_instance


@pytest.fixture
def mock_browser() -> Browser:
    mock_instance = AsyncMock(spec=Browser)
    mock_instance.click.side_effect = lambda label: f"clicked on {label}"
    mock_instance.fill.side_effect = lambda field, value: f"filled '{value}' in {field}"
    mock_instance.select.side_effect = (
        lambda field, value: f"selected '{value}' in {field}"
    )
    mock_instance.goto.side_effect = lambda url: f"navigated to '{url}'"
    mock_instance.vertical_scroll.side_effect = (
        lambda direction: f"Scrolled '{direction}'"
    )
    mock_instance.screenshot.side_effect = [b"1", b"2", b"3"]
    mock_instance.mark_page = AsyncMock()

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
async def test_user_prompt(empty_actor: Actor, mock_actor_input: ActorInput):
    """Test main prompt builds itself"""
    prompt = empty_actor._build_user_prompt(mock_actor_input)
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
    fake_screenshot = b"screen"
    empty_actor._setup_conversation(mock_actor_input, fake_screenshot)
    assert empty_actor.conversation[0].role == MessageRole.System
    assert (
        "Your role is to perform the provided query"
        in empty_actor.conversation[0].content
    )
    assert empty_actor.conversation[0].screenshot is None
    assert empty_actor.conversation[1].role == MessageRole.User
    assert (
        "Your role is to analyze the current state of the web application"
        in empty_actor.conversation[1].content
    )
    assert empty_actor.conversation[1].screenshot == [fake_screenshot]


@pytest.mark.asyncio
async def test_actor_process_3_rounds(
    mock_llm_client: LLMClient,
    mock_browser: Browser,
    mock_actor_input: ActorInput,
):
    with (
        patch("VTAAS.workers.actor.LLMClient", return_value=mock_llm_client),
        patch(
            "VTAAS.workers.actor.add_banner", return_value=b"banner_screenshot"
        ) as mock_add_banner,
    ):
        actor = Actor(query="Test Query", browser=mock_browser)
        result: WorkerResult = await actor.process(mock_actor_input)

        assert isinstance(result, ActorResult)
        assert result.status == "success"
        assert result.explaination == "Logged in as hello_AI"
        assert len(result.actions) == 2

        mock_add_banner.assert_called()
        assert isinstance(result.screenshot, bytes)
        assert result.screenshot == b"banner_screenshot"

        mock_browser = cast(AsyncMock, mock_browser)
        mock_browser.mark_page.assert_awaited()
        mock_browser.screenshot.assert_awaited()
        mock_browser.click.assert_called_with("2")
        mock_browser.fill.assert_called_with("3", "hello_AI")

        mock_llm_client = cast(AsyncMock, mock_llm_client)
        assert mock_llm_client.act.call_count == 3


@pytest.mark.asyncio
@pytest.mark.llm
async def test_integ():
    logging.getLogger("VTAAS.worker.actor").setLevel(logging.DEBUG)
    url = "http://www.vtaas-benchmark.com:7770/"
    test_collection = TestCaseCollection("data/OneStop_Passing.csv", url)
    test_case = test_collection.get_test_case_by_id("1")
    test_step = test_case.get_step(2)
    query = "click on the 'Sign in' link"
    actor_input = ActorInput(
        test_case=str(test_case), test_step=test_step, history=None
    )
    async with async_playwright() as p:
        browser = await Browser.create(
            id="actor_test_integ_browser",
            headless=False,
            playwright=p,
            save_screenshot=True,
        )
        _ = await browser.goto(url)
        actor = Actor(query, browser)
        verdict = await actor.process(actor_input)
        print(verdict)
        assert verdict.status == Status.PASS
