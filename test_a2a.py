import asyncio
import os
import uuid
import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import AgentCard, Message, Part, Role, TextPart, TransportProtocol

async def main():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    
    resource = "projects/109757236593/locations/us-east1/reasoningEngines/1463474165825667072"
    a2a_base = f"https://us-east1-aiplatform.googleapis.com/reasoningEngines/v1/{resource}/api/a2a/wanderlust_planner"
    card_url = f"{a2a_base}/.well-known/agent-card.json"
    
    async with httpx.AsyncClient(headers=headers, timeout=120) as client:
        resp = await client.get(card_url)
        card = AgentCard(**resp.json())
        card.url = a2a_base
        
        factory = ClientFactory(
            ClientConfig(
                supported_transports=[TransportProtocol.jsonrpc, TransportProtocol.http_json],
                httpx_client=client,
            )
        )
        a2a_client = factory.create(card)
        
        msg = Message(message_id=str(uuid.uuid4()), role=Role.user, parts=[Part(root=TextPart(text="hi"))])
        async for event in a2a_client.send_message(msg):
            print("EVENT:", event)

asyncio.run(main())
