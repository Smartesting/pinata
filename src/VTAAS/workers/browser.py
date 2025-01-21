from typing import Literal, NotRequired, TypeAlias, TypeVar, TypedDict, final
import playwright.async_api as pw
from urllib.parse import urlparse
from VTAAS.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound="Browser")

ScrollDirection: TypeAlias = Literal["up", "down"]


class ScreenshotResult(TypedDict):
    screenshot: NotRequired[bytes]
    error: NotRequired[str]


class MarkResult(TypedDict):
    locator: NotRequired[pw.Locator]
    error: NotRequired[str]


@final
class Browser:
    """Playwright based Browser"""

    def __init__(self, name: str, headless: bool):
        self.id = name
        self.scrolled_to: int = -1
        self._browser: pw.Browser | None = None
        self._context: pw.BrowserContext | None = None
        self._page: pw.Page | None = None
        self._headless = headless
        logger.info(f"Browser {self.id} instanciated")

    async def initialize(self, playwright: pw.Playwright | None) -> None:
        """Initialize the browser instance"""
        if playwright is None:
            playwright = await pw.async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(bypass_csp=True)
        await self._context.add_init_script(path="./js/mark_page.js")
        self._page = await self._context.new_page()
        # _ = await self._page.wait_for_function("() => typeof markPage === 'function'")
        logger.info(f"Browser {self.id} started")

    @classmethod
    async def create(
        cls: type[T],
        name: str,
        headless: bool = True,
        playwright: pw.Playwright | None = None,
    ) -> T:
        """Class method to create and initialize a Browser instance"""
        instance = cls(name, headless)
        await instance.initialize(playwright)
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

    async def goto(self, url: str) -> str:
        """Navigate to a URL"""
        if not self._is_valid_url(url):
            return "Invalid URL"
        try:
            response = await self.page.goto(url, wait_until="commit")
            if response and response.ok:
                return f"Successfully navigated to {url}"
            else:
                status = response.status if response else "unknown"
                return f"Navigate to {url} but page return an {status} status"
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return f"An error happened while navigating to {url}"

    async def select(self, mark: str, *values: str) -> str:
        """
        Select options in a dropdown element identified by its label
        """
        result = await self._resolve_mark(mark)
        if "error" in result or "locator" not in result:
            return result.get("error", "Unknown error")

        locator = result["locator"]
        try:
            result = await locator.select_option(values)
            if result:
                outcome = f'Options "{", ".join(values)}" have been selected'
            else:
                outcome = "No option selected"
            return outcome

        except Exception as e:
            error_msg = str(e)
            if "did not find some options" in error_msg:
                available_options = await locator.evaluate("""
                    (element) => {
                        if (element instanceof HTMLSelectElement) {
                            return Array.from(element.options).map(option => option.value);
                        } else return []
                    }
                """)

                available_options_str = (
                    ", ".join(available_options) if available_options else "unknown"
                )
                return (
                    f"The select element exists but does not contain the provided option. "
                    f"Available options: {available_options_str}. "
                )

            return "The label does not seem to match a <select> element. Maybe it is a styled DIV?"

    async def screenshot(self) -> ScreenshotResult:
        try:
            screenshotBuffer = await self.page.screenshot()
            return {
                "screenshot": screenshotBuffer,
            }

        except Exception as e:
            logger.error(f"Screenshot error: {str(e)}")
            return {"error": "An error happened while taking screenshot"}

    async def mark_page(self):
        await self.page.evaluate("markPage()")

    async def get_marked_elements(self) -> str:
        return await self.page.evaluate("""async () => {
          const marks: Array<{ mark: string; element: string }> = []
          document.querySelectorAll('[data-mark]').forEach((e) => {
            const attributes = Array.from(e.attributes)
              .map((attr) => (['data-mark'].includes(attr.name) ? '' : `${attr.name}="${attr.value}"`))
              .join(' ')
            let element: string
            if (e.tagName.toLowerCase() === 'select') {
              const options = Array.from(e.children)
                .filter((child) => child.tagName.toLowerCase() === 'option')
                .map((option) => option.textContent?.trim())
                .join(', ')
              element = `<${e.tagName.toLowerCase()} ${attributes}>${options}</${e.tagName.toLowerCase()}>`
            } else {
              const innerText = e.textContent?.trim()
              element =
                `<${e.tagName.toLowerCase()} ${attributes}>` +
                innerText +
                `</${e.tagName.toLowerCase()}>`
            }
            marks.push({ mark: e.getAttribute('data-mark') ?? '', element })
          })
          return marks
        }""")

    async def get_page_info(self) -> str:
        """Get current page information"""
        title = await self.page.title()
        url = self.page.url
        return f"Current URL: {url}\nPage title: {title}"

    async def close(self) -> None:
        """Close the browser instance"""
        if self.page:
            await self.page.close()
        if self._browser:
            await self._browser.close()

    async def _resolve_mark(self, mark: str) -> MarkResult:
        """
        Resolve a mark to a Playwright locator
        """
        locators = await self.page.locator(f'[data-mark="{mark}"]').all()
        if len(locators) < 1:
            return {
                "error": "This label does not exist",
            }
        try:
            locator = self.page.get_by_label(mark)
            return {"locator": locator}
        except Exception as e:
            return {"error": f"Could not resolve label: {str(e)}"}

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return bool(result.netloc)
        except Exception:
            return False
