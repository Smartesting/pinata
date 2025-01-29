import pytest
from VTAAS.data.testcase import TestCaseCollection
from VTAAS.orchestrator import Orchestrator


@pytest.mark.asyncio
@pytest.mark.llm
async def test_one_TC():
    test_collection = TestCaseCollection(
        "data/OneStop_Passing.csv", "http://www.vtaas-benchmark.com:7770/"
    )
    test_case = test_collection.get_test_case_by_id("1")
    orchestrator = Orchestrator()

    _ = await orchestrator.process_TestCase(test_case)
    # Initialize workers based on a specific task
    # await orchestrator.initialize_workers(
    #     context="Processing a large dataset of customer transactions",
    #     objective="Identify and flag suspicious transactions while monitoring system performance",
    # )
