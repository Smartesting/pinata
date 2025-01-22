import pytest
from VTAAS.data.testcase import TestCaseCollection
from VTAAS.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_one_TC():
    # Create orchestrator
    orchestrator = Orchestrator()

    test_collection = TestCaseCollection("data/OneStop_Passing.csv")
    # Get test cases in different ways
    test_case = test_collection.get_test_case_by_id("28")

    await orchestrator.process_TestCase(test_case)
    # Initialize workers based on a specific task
    # await orchestrator.initialize_workers(
    #     context="Processing a large dataset of customer transactions",
    #     objective="Identify and flag suspicious transactions while monitoring system performance",
    # )
