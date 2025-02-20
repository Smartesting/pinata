import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time
from playwright.async_api import async_playwright

if __name__ == "__main__":
    sys.path.append(os.path.join(str(Path(__file__).parent), "src"))

from VTAAS.data.testcase import TestCase
from VTAAS.llm.llm_client import LLMProvider
from VTAAS.orchestrator.orchestrator import Orchestrator
from VTAAS.schemas.verdict import Status
from VTAAS.workers.browser import Browser


def deserialize_test_case(
    json_file_path: str, output_folder: str = "output"
) -> TestCase:
    with open(json_file_path, "r") as file:
        data = json.load(file)

    actions = [action["action"] for action in data["actions"]]
    expected_results = [action["expectedResult"] for action in data["actions"]]

    test_case = TestCase(
        full_name=data["name"],
        actions=actions,
        expected_results=expected_results,
        url=data["url"],
        failing_info=None,
        output_folder=output_folder,
    )

    return test_case


async def run_testcase(test_case: TestCase, output_folder: str, provider: str):
    async with async_playwright() as p:
        browser = await Browser.create(
            id="actor_test_integ_browser",
            headless=False,
            playwright=p,
            save_screenshot=False,
            tracer=False,
            trace_folder=output_folder,
        )

        llm_provider: LLMProvider = LLMProvider.OPENAI
        match provider:
            case "openai":
                llm_provider = LLMProvider.OPENAI
            case "anthropic":
                llm_provider = LLMProvider.ANTHROPIC
            case "google":
                llm_provider = LLMProvider.GOOGLE
            case "mistral":
                llm_provider = LLMProvider.MISTRAL
            case "openrouter":
                llm_provider = LLMProvider.OPENROUTER
            case _:
                raise ValueError("Provider does not exist")

        orchestrator = Orchestrator(
            browser=browser,
            llm_provider=llm_provider,
            tracer=True,
            output_folder=output_folder,
        )

        execution_result = await orchestrator.process_testcase(test_case)

        if execution_result.status == Status.PASS:
            print("SUCCESS!")
        else:
            print("FAIL!")


async def main():
    parser = argparse.ArgumentParser(description="Run a test case from a JSON file")
    _ = parser.add_argument(
        "-f", "--file", required=True, help="Path to the test case JSON file"
    )
    _ = parser.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic", "google", "mistral", "openrouter"],
        default="openai",
    )
    output_folder = (
        Path("/tmp") / f"{str(parser.__hash__())[:8]}_{str(time.time())[:8]}"
    )
    output_folder.mkdir(exist_ok=True)
    print(f"execution logs will be stored at {output_folder}")

    args = parser.parse_args()
    testcase: TestCase = deserialize_test_case(args.file, str(output_folder))

    try:
        await run_testcase(testcase, str(output_folder), args.provider)

    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
