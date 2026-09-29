import asyncio
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import AgentCard

async def main():
    async with httpx.AsyncClient() as client:
        # Just instantiate the factory to see what protocol it uses
        print("Ready")

asyncio.run(main())
