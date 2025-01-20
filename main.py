import asyncio

from src.orchestrator.orchestrator import Orchestrator


async def main():
    orchestrator = Orchestrator()
    results = await orchestrator.spawn_and_process(
        context="Your context here", data="Your data to process"
    )
    print(results)


# Run the async code
asyncio.run(main())
