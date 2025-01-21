from typing import Literal, TypeAlias, TypeVar, TypedDict, final
import playwright.async_api as pw
from urllib.parse import urlparse
from VTAAS.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound="Browser")

ScrollDirection: TypeAlias = Literal["up", "down"]


class ViewportData(TypedDict):
    scrollX: int
    scrollY: int
    viewportWidth: int
    viewportHeight: int
    pageWidth: int
    pageHeight: int


class ScreenshotResult(TypedDict, total=False):
    screenshot: bytes
    info: str
    error: str


class ActionResult(TypedDict, total=False):
    success: str
    fail: str


@final
class Browser:
    """Playwright based Browser"""

    def __init__(self, name: str):
        self.id = name
        self.scrolled_to: int = -1
        self._browser: pw.Browser | None = None
        self._page: pw.Page | None = None
        logger.info(f"Browser {self.id} initialized")

    async def initialize(self) -> None:
        """Initialize the browser instance"""
        playwright = await pw.async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=True)
        self._page = await self._browser.new_page()
        logger.info(f"Browser {self.id} started")

    @classmethod
    async def create(cls: type[T], name: str) -> T:
        """Class method to create and initialize a Browser instance"""
        instance = cls(name)
        await instance.initialize()
        return instance

    @property
    def browser(self) -> pw.Browser:
        """Get the browser instance, ensuring it is initialized"""
        if self._browser is None:
            raise RuntimeError(
                "Browser has not been initialized yet. Do Browser.create(name)."
            )
        return self._browser

    @property
    def page(self) -> pw.Page:
        """Get the page instance, ensuring it is initialized"""
        if self._page is None:
            raise RuntimeError(
                "Browser has not been initialized yet. Do Browser.create(name)."
            )
        return self._page

    async def goto(self, url: str) -> ActionResult:
        """Navigate to a URL"""
        if not self._is_valid_url(url):
            return {"fail": "Invalid URL"}
        try:
            response = await self.page.goto(url, wait_until="commit")
            if response and response.ok:
                return {"success": f"Successfully navigated to {url}"}
            else:
                status = response.status if response else "unknown"
                return {
                    "success": f"Navigate to {url} but page return an {status} status"
                }
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return {"fail": f"An error happened while navigating to {url}"}

    async def close(self) -> None:
        """Close the browser instance"""
        if self.page:
            await self.page.close()
        if self._browser:
            await self._browser.close()

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return bool(result.netloc)
        except Exception:
            return False
