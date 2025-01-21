import asyncio
from time import sleep

from playwright.async_api import async_playwright
from VTAAS.workers.browser import Browser


async def main():
    async with async_playwright() as p:
        browser = await Browser.create("test_browser", False, p)
        try:
            print("it should spawn a browser")
            browser_outcome = await browser.goto("https://www.smartesting.com")
            print(f"goto: {browser_outcome}")
            _ = await browser.mark_page()
            elements = await browser.get_marks()
            print(f"marks: {str(elements)}")
            sleep(5)
        except Exception as e:
            print(f"error: {str(e)}")
        finally:
            await browser.close()


asyncio.run(main())
