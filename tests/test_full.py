import pytest
from VTAAS.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_actor_processing():
    # Create orchestrator
    orchestrator = Orchestrator()

    # Initialize workers based on a specific task
    await orchestrator.initialize_workers(
        context="Processing a large dataset of customer transactions",
        objective="Identify and flag suspicious transactions while monitoring system performance",
    )

    # Process some data
    await orchestrator.spawn_and_process(
        "Wasabi is the new context",
        {"transaction_id": "123", "amount": 1000, "timestamp": "2023-08-17T10:00:00Z"},
    )

    print("Processing results: DONE")
