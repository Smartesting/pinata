import logging
from playwright.async_api import async_playwright
import pytest
from VTAAS.data.testcase import TestCaseCollection
from VTAAS.llm.llm_client import LLMProviders
from VTAAS.orchestrator import Orchestrator
from VTAAS.workers.browser import Browser


@pytest.mark.asyncio
@pytest.mark.llm
async def test_one_TC():
    async with async_playwright() as p:
        browser = await Browser.create(
            id="actor_test_integ_browser",
            headless=False,
            playwright=p,
            save_screenshot=True,
        )
        test_collection = TestCaseCollection(
            "data/OneStop_Passing.csv", "http://www.vtaas-benchmark.com:7770/"
        )
        test_case = test_collection.get_test_case_by_id("1")
        orchestrator = Orchestrator(
            browser=browser, llm_provider=LLMProviders.ANTHROPIC
        )
        orchestrator.logger.setLevel(logging.DEBUG)

        _ = await orchestrator.process_testcase(test_case)
    # Initialize workers based on a specific task
    # await orchestrator.initialize_workers(
    #     context="Processing a large dataset of customer transactions",
    #     objective="Identify and flag suspicious transactions while monitoring system performance",
    # )
