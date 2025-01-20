import pytest
from src.orchestrator.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_llm_spawn():
    orchestrator = Orchestrator()

    # Test the full flow
    results = await orchestrator.spawn_and_process(
        context="Test context", data="test_data"
    )

    # Check results (based on our dummy LLM response of ["actor", "observer", "actor", "observer"])
    assert len(results) == 4
    assert any("Actor" in result for result in results)
    assert any("Observer" in result for result in results)

    # Check if workers were created
    assert len(orchestrator.actors) == 2
    assert len(orchestrator.observers) == 2


@pytest.mark.asyncio
async def test_actor_processing():
    orchestrator = Orchestrator()
    actor = orchestrator.spawn_actor("test_actor")

    result = await actor.process("test_data")
    assert "Actor" in result
    assert "test_data" in result


@pytest.mark.asyncio
async def test_observer_processing():
    orchestrator = Orchestrator()
    observer = orchestrator.spawn_observer("test_observer")

    result = await observer.process("test_data")
    assert "Observer" in result
    assert "test_data" in result
