import re
import pytest
import pytest_asyncio
from collections.abc import AsyncGenerator
from playwright.async_api import Browser as PWBrowser, Page
from workers.browser import Browser


@pytest_asyncio.fixture
async def browser() -> AsyncGenerator[Browser, None]:
    """create and cleanup a browser"""
    browser_instance = await Browser.create("test_browser")
    yield browser_instance
    await browser_instance.close()


@pytest.mark.asyncio
async def test_browser_initialization():
    """Test initialization"""
    browser = await Browser.create("test_browser")
    try:
        assert browser.id == "test_browser"
        assert browser.scrolled_to == -1
        assert isinstance(browser.browser, PWBrowser)
        assert isinstance(browser.page, Page)
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_browser_properties_before_initialization():
    """Test can't access page and browser if create has not been called"""
    browser = Browser("test_browser")  # Not initialized

    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "Browser has not been initialized yet. Do Browser.create(name)."
        ),
    ):
        _ = browser.browser

    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "Browser has not been initialized yet. Do Browser.create(name)."
        ),
    ):
        _ = browser.page


@pytest.mark.asyncio
async def test_goto_valid_url(browser: Browser):
    """Test navigation to a valid URL"""
    result = await browser.goto("https://www.example.com")
    assert "success" in result
    assert "Successfully navigated to https://www.example.com" in result["success"]


@pytest.mark.asyncio
async def test_goto_invalid_url(browser: Browser):
    """Test navigation to an invalid URL"""
    result = await browser.goto("not-a-valid-url")
    assert "fail" in result
    assert "Invalid URL" in result["fail"]


@pytest.mark.asyncio
async def test_goto_nonexistent_domain(browser: Browser):
    """Test navigation to a nonexistent domain"""
    result = await browser.goto("https://nonex1stent-domain-name-25115.com")
    assert "fail" in result
    assert "An error happened while navigating to" in result["fail"]
