from typing import (
    Literal,
    NotRequired,
    TypeAlias,
    TypeVar,
    TypedDict,
    Unpack,
    cast,
    final,
)
from uuid import uuid4
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


class BrowserParams(TypedDict):
    playwright: pw.Playwright | None
    headless: bool
    timeout: int
    id: str


class ScreenshotResult(TypedDict):
    screenshot: NotRequired[bytes]
    error: NotRequired[str]


class Mark(TypedDict):
    mark: str
    element: str


class MarkLocatorResult(TypedDict):
    locator: NotRequired[pw.Locator]
    error: NotRequired[str]


@final
class Browser:
    """Playwright based Browser"""

    def __init__(self, **kwargs: Unpack[BrowserParams]):
        default_browser_params: BrowserParams = {
            "headless": True,
            "timeout": 3000,
            "id": uuid4().hex,
            "playwright": None,
        }
        custom_params = kwargs
        if custom_params and set(custom_params.keys()).issubset(
            set(default_browser_params.keys())
        ):
            default_browser_params.update(custom_params)
        elif custom_params:
            raise ValueError("unknown browser parameter(s) received")

        self._params = default_browser_params
        self._scrolled_to: int = -1
        self._browser: pw.Browser | None = None
        self._context: pw.BrowserContext | None = None
        self._page: pw.Page | None = None
        logger.info(f"Browser {self.id} instanciated")

    async def initialize(self) -> None:
        """Initialize the browser instance"""
        if self._params["playwright"] is None:
            self._params["playwright"] = await pw.async_playwright().start()
        self._browser = await self._params["playwright"].chromium.launch(
            headless=self._params["headless"],
        )
        self._context = await self._browser.new_context(bypass_csp=True)
        self._context.set_default_timeout(self._params["timeout"])
        self._page = await self._context.new_page()

        self._page.on("load", lambda load: self.load_js())
        self._page.on("framenavigated", lambda load: self.load_js())
        logger.info(f"Browser {self.id} started")

    async def load_js(self):
        _ = await self.page.add_script_tag(path="./js/mark_page.js")
        _ = await self.page.wait_for_function(
            "() => typeof window.markPage === 'function'"
        )
        _ = await self.page.add_script_tag(path="./js/element_to_html_string.js")
        _ = await self.page.wait_for_function(
            "() => typeof window.elementToHtmlString  === 'function'"
        )

    @classmethod
    async def create(cls: type[T], **kwargs: Unpack[BrowserParams]) -> T:
        """Class method to create and initialize a Browser instance"""
        instance = cls(**kwargs)
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

    @property
    def scrolled_to(self) -> int:
        """Get the maximum scroll value for the current page"""
        return self._scrolled_to

    @property
    def id(self) -> str:
        """Get the maximum scroll value for the current page"""
        return self._params["id"]

    async def goto(self, url: str) -> str:
        """Navigate to a URL"""
        if not self._is_valid_url(url):
            return "Invalid URL"
        try:
            response = await self.page.goto(url, wait_until="networkidle")
            if response and response.ok:
                return f"Successfully navigated to {url}"
            else:
                status = response.status if response else "unknown"
                return f"Navigate to {url} but page return an {status} status"
        except Exception as e:
            logger.error(f"Navigation error: {str(e)}")
            return f"An error happened while navigating to {url}"

    async def click(self, mark: str) -> str:
        before_url = self.page.url
        outcome = ""

        result = await self._resolve_mark(mark)
        if "error" in result or "locator" not in result:
            return result.get("error", "Unknown error")

        locator = result["locator"]
        html_element_str = await self.get_html_element_from_locator(result["locator"])
        outcome += f"Clicked on ['{mark}'] ==> {html_element_str}. "

        try:
            await locator.click()
            await self.page.wait_for_load_state("domcontentloaded")
        except Exception as error:
            return f"Unable to click on element '{mark}' due to a timeout or error: {error}"

        after_url = self.page.url
        is_url_effect = before_url != after_url
        if is_url_effect:
            outcome += f"A page change occurred. New URL: {after_url}"

        return outcome.strip()

    async def fill(self, mark: str, value: str) -> str:
        result = await self._resolve_mark(mark)
        if "error" in result or "locator" not in result:
            return result.get("error", "Unknown error")

        locator = result["locator"]
        html_element_str = await self.get_html_element_from_locator(result["locator"])
        tag: str = await locator.evaluate("element => element.nodeName")

        try:
            if (
                tag == "INPUT"
                and await locator.evaluate("element => element.type") == "date"
            ):
                await locator.fill(value)
            elif tag == "SELECT":
                _ = await locator.select_option(value)
            else:
                await locator.clear()
                await locator.type(value)

            typed_value = await locator.input_value()
            if typed_value == value:
                outcome = (
                    f"Filled value {value} in element [{mark}] ==> {html_element_str}"
                )
                return outcome

            return f"Could not fill {html_element_str} element. Are you sure this is the right label?"
        except Exception as e:
            print(e)
            return f"There was an error while filling {html_element_str} element."

    async def vertical_scroll(self, direction: str, pixels: int = 450) -> str:
        """Scroll the page vertically"""
        if pixels < 0:
            return "negative pixel values not allowed."
        if pixels < 10:
            return "Pixel value is too low. Expecting 10 or more."
        viewport_data = await self._get_viewport_data()
        scroll_y = viewport_data["scrollY"]
        viewport_height = viewport_data["viewportHeight"]
        page_height = viewport_data["pageHeight"]

        try:
            match direction:
                case "up":
                    print(
                        f"page_height: {page_height}, viewport_height: {viewport_height}, scroll_y: {scroll_y}"
                    )
                    if scroll_y == 0:
                        return (
                            "You can't scroll up: you're already at the top of the page"
                        )
                    await self.page.mouse.wheel(0, -pixels)
                    _ = await self.page.wait_for_function(
                        f"window.scrollY === {scroll_y - pixels}"
                    )

                case "down":
                    if scroll_y >= page_height - viewport_height - 10:
                        return "You can't scroll down: you're already at the bottom of the page"
                    self._scrolled_to += pixels
                    await self.page.mouse.wheel(0, pixels)
                    _ = await self.page.wait_for_function(
                        f"window.scrollY === {scroll_y + pixels}"
                    )

                case _:
                    return 'Invalid direction. Expected "up" or "down".'

            return f"Successfully scrolled {pixels} {direction}"

        except Exception as e:
            error_msg = f"An error happened while scrolling {pixels} {direction}"
            logger.error(f"{error_msg}: {str(e)}")
            return error_msg

    async def select(self, mark: str, *values: str) -> str:
        """
        Select options in a dropdown element identified by its label
        """
        if not values:
            return "Missing option(s) to select"

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
                available_options: list[str] = await locator.evaluate("""
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

    async def screenshot(self) -> bytes:
        try:
            return await self.page.screenshot()

        except Exception as e:
            logger.error(f"Screenshot error: {str(e)}")
            return b""

    async def mark_page(self):
        _ = await self.page.wait_for_function(
            "() => typeof window.markPage === 'function'"
        )
        await self.page.evaluate("window.markPage()")

    async def get_marks(self) -> list[Mark]:
        return cast(
            list[Mark],
            await self.page.evaluate("""async () => {
          const marks = []
          document.querySelectorAll('[data-mark]').forEach((e) => {
            marks.push({ mark: e.getAttribute('data-mark'), element: window.elementToHtmlString(e) })
          })
          return marks
        }"""),
        )

    async def get_html_element_from_locator(self, locator: pw.Locator) -> str:
        _ = await self.page.wait_for_function(
            "() => typeof window.elementToHtmlString === 'function'"
        )
        element: str = await locator.evaluate(
            """(element) => window.elementToHtmlString(element)"""
        )
        return element

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

    async def _resolve_mark(self, mark: str) -> MarkLocatorResult:
        """
        Resolve a mark to a Playwright locator
        """
        try:
            locators = await self.page.locator(f'[data-mark="{mark}"]').all()
            if len(locators) < 1:
                return {
                    "error": "This mark does not exist",
                }
            return {"locator": locators[0]}
        except Exception as e:
            return {"error": f"Could not resolve mark: {str(e)}"}

    async def _get_viewport_data(self) -> ViewportData:
        """Get viewport related data"""
        return cast(
            ViewportData,
            await self.page.evaluate("""
            () => ({
                scrollX: window.scrollX,
                scrollY: window.scrollY,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                pageWidth: document.documentElement.scrollWidth,
                pageHeight: document.documentElement.scrollHeight
            })
        """),
        )

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        try:
            result = urlparse(url)
            return bool(result.scheme in ["http", "https"] and result.netloc)
        except Exception:
            return False
