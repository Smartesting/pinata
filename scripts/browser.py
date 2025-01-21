from workers.browser import Browser


async def launch_and_browse():
    browser = await Browser.create("test_browser", False)
    try:
        _ = await browser.goto("www.smartesting.com")
    finally:
        await browser.close()
