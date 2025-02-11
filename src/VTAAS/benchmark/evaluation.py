import asyncio
from pathlib import Path
import sys
from playwright.async_api import async_playwright

# Add parent directory to path for relative imports when running as script
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent.parent))


from VTAAS.data.testcase import TestCaseCollection
from VTAAS.llm.llm_client import LLMProviders
from VTAAS.orchestrator.orchestrator import Orchestrator
from VTAAS.schemas.verdict import Status
from VTAAS.workers.browser import Browser


async def run_evaluation(
    tc_collection: TestCaseCollection, browser: Browser
) -> dict[str, float]:
    metrics: dict[str, float] = {}

    metrics["FN"] = 0
    metrics["TN"] = 0
    metrics["FP"] = 0
    metrics["AFA"] = 0
    metrics["AFB"] = 0
    metrics["AFC"] = 0

    for test_case in tc_collection:
        orchestrator = Orchestrator(browser=browser, llm_provider=LLMProviders.OPENAI)

        execution_result = await orchestrator.process_testcase(test_case)

        if execution_result.status == Status.PASS:
            if test_case.type == "F":
                metrics["FN"] = metrics["FN"] + 1
            elif test_case.type == "P":
                print("TN")

        else:
            if test_case.type == "F":
                match execution_result.step_index:
                    case _ if execution_result.step_index < test_case.failing_step:
                        metrics["AFB"] = metrics["AFB"] + 1
                    case _ if execution_result.step_index == test_case.failing_step:
                        metrics["AFC"] = metrics["AFC"] + 1
                    case _ if execution_result.step_index > test_case.failing_step:
                        metrics["AFA"] = metrics["AFA"] + 1

            elif test_case.type == "P":
                metrics["FP"] = metrics["FP"] + 1

    metrics["TP"] = metrics["AFA"] + metrics["AFB"] + metrics["AFC"]
    metrics["accuracy"] = (metrics["TP"] + metrics["TN"]) / (
        metrics["TP"] + metrics["TN"] + metrics["FP"] + metrics["FN"]
    )
    metrics["specificity"] = metrics["TN"] / (metrics["TN"] + metrics["FP"])
    metrics["sensitivity"] = metrics["TP"] / (metrics["TP"] + metrics["FN"])
    metrics["AER"] = metrics["AFB"] / metrics["TP"]
    metrics["HER"] = metrics["AFA"] / metrics["TP"]
    metrics["SMER"] = metrics["AER"] + metrics["HER"]
    metrics["truacc"] = (metrics["AFC"] + metrics["TN"]) / (
        metrics["TP"] + metrics["TN"] + metrics["FP"] + metrics["FN"]
    )

    return metrics


async def main():
    async with async_playwright() as p:
        browser = await Browser.create(
            id="actor_test_integ_browser",
            headless=False,
            playwright=p,
            save_screenshot=True,
        )
        test_collection = TestCaseCollection(
            "data/Benchmark - OneStopMarket.xlsx - Failing - redux.csv",
            "http://www.vtaas-benchmark.com:7770/",
        )

        metrics = await run_evaluation(test_collection, browser)
        print(metrics)


if __name__ == "__main__":
    asyncio.run(main())
