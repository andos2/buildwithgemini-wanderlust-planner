import asyncio
import httpx
import uuid
import google.auth
import google.auth.transport.requests

async def main():
    creds, _ = google.auth.default()
    creds.refresh(google.auth.transport.requests.Request())
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
    
    url = "https://us-east1-aiplatform.googleapis.com/reasoningEngines/v1/projects/109757236593/locations/us-east1/reasoningEngines/1463474165825667072/api/a2a/wanderlust_planner"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "a2a.sendMessage",
        "params": {
            "message": {
                "message_id": str(uuid.uuid4()),
                "role": "USER",
                "parts": [{"text": "hi"}],
                "context_id": "test_ctx_1"
            }
        },
        "id": "1"
    }
    
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url, headers=headers, json=payload, timeout=60) as resp:
            print("Status:", resp.status_code)
            async for line in resp.aiter_lines():
                if line.strip():
                    print("LINE:", line)

asyncio.run(main())
