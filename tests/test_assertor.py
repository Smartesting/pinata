import logging
import time
from typing import cast
from unittest.mock import Mock

import pytest
from playwright.async_api import async_playwright
from pytest_mock import MockerFixture

from VTAAS.data.testcase import TestCaseCollection
from VTAAS.llm.llm_client import LLMClient, LLMProvider
from VTAAS.schemas.verdict import Status
from VTAAS.schemas.worker import AssertorInput, MessageRole
from VTAAS.workers.assertor import Assertor
from VTAAS.workers.browser import Browser

MOCKED_ASSERTION = "This is a mocked assertion"


@pytest.fixture
def mock_llm_client(mocker: MockerFixture) -> LLMClient:
    mocked_class = mocker.patch("VTAAS.workers.assertor.LLMClient", autospec=True)
    mock_instance: LLMClient = cast(LLMClient, mocked_class.return_value)

    mock_instance.plan_step = Mock()
    # mock_instance.get_worker_configs.return_value = [...]

    return mock_instance


@pytest.fixture
def mock_browser(mocker: MockerFixture) -> Browser:
    mocked_class = mocker.patch("VTAAS.workers.assertor.Browser", autospec=True)
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
def mock_assertion() -> str:
    return MOCKED_ASSERTION


@pytest.fixture
def mock_assertor_input() -> AssertorInput:
    return AssertorInput(
        test_case="TC-1-P: Login & Logout\n1. login\n2.logout",
        test_step=("1. login", ""),
        history="filled 'user' in username field",
    )


@pytest.fixture
def empty_assertor(mock_assertion: str, mock_browser: Browser) -> Assertor:
    return Assertor(mock_assertion, mock_browser, llm_provider=LLMProvider.OPENAI)


@pytest.mark.asyncio
async def test_main_prompt(
    empty_assertor: Assertor, mock_assertor_input: AssertorInput
):
    """Test main prompt builds itself"""
    prompt = empty_assertor._build_user_prompt(mock_assertor_input)
    current_step = (
        mock_assertor_input.test_step[0] + "; " + mock_assertor_input.test_step[1]
    )
    assert f"<test_case>\n{mock_assertor_input.test_case}\n</test_case>" in prompt
    assert f"<current_step>\n{current_step}\n</current_step>" in prompt
    assert f"<assertion>\n{MOCKED_ASSERTION}\n</assertion>" in prompt


@pytest.mark.asyncio
async def test_conversation(
    empty_assertor: Assertor, mock_assertor_input: AssertorInput
):
    """Test main prompt builds itself"""
    fake_screenshot = b"screen"
    empty_assertor._setup_conversation(mock_assertor_input, fake_screenshot)
    assert empty_assertor.conversation[0].role == MessageRole.System
    assert (
        "Your role is to assert the expected state"
        in empty_assertor.conversation[0].content
    )
    assert empty_assertor.conversation[0].screenshot is None
    assert empty_assertor.conversation[1].role == MessageRole.User
    assert (
        "Your role is to verify assertions based on a screenshot"
        in empty_assertor.conversation[1].content
    )
    assert empty_assertor.conversation[1].screenshot == [fake_screenshot]


@pytest.mark.asyncio
@pytest.mark.llm
async def test_integ():
    logging.getLogger("VTAAS.worker.assertor").setLevel(logging.DEBUG)
    url = "http://www.vtaas-benchmark.com:9999/"
    test_collection = TestCaseCollection("./benchmark/postmill_passing.csv", url)
    test_case = test_collection.get_test_case_by_id("1")
    test_step = test_case.get_step(1)
    # assertion = "The page contains a 'Create an Account' link at the top right corner"
    assertion = "The page contains a search field"
    assertor_input = AssertorInput(
        test_case=str(test_case), test_step=test_step, history=None
    )
    async with async_playwright() as p:
        browser = await Browser.create(
            id="assertor_test_integ_browser",
            headless=False,
            playwright=p,
            save_screenshot=True,
        )
        _ = await browser.goto(url)
        assertor = Assertor(
            query=assertion,
            browser=browser,
            llm_provider=LLMProvider.OPENROUTER,
            start_time=time.time(),
            output_folder=f"/tmp/{str(browser.__hash__())[:8]}",
        )
        verdict = await assertor.process(assertor_input)
        assert verdict.status == Status.PASS
