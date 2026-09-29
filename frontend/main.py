"""Minimal FastAPI proxy for a deployed A2A agent (Agent Runtime, agents-cli 1.1.0+).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy authenticates with Application Default Credentials and
forwards chat to the deployed agent over the A2A protocol, returning replies as
structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.

Why A2A: agents-cli 1.1.0 (GA) deploys ADK agents to Agent Runtime as A2A agents
and no longer registers the reasoning-engine operation schema the old
`agent_engines.get(...).stream_query()` path relied on (operation_schemas() comes
back empty). The container serves the A2A protocol over the Agent Engine HTTP
passthrough, so this proxy fetches the agent's card and sends messages with the
a2a-sdk client (the same path `agents-cli run --mode a2a` uses). This works for
both A2A and plain ADK 1.1.0 deployments (the container serves A2A either way).

Run:
  pip install -r requirements.txt
  export AGENT_ENGINE_RESOURCE_NAME="projects/.../locations/.../reasoningEngines/..."
  export AGENT_DIRECTORY="app"   # your agent's app directory (agents-cli-manifest.yaml)
  python main.py                 # -> http://localhost:8080
"""

import os
import uuid

import google.auth
import google.auth.transport.requests
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Part,
    SendMessageRequest,
    Role,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

RESOURCE = os.environ["AGENT_ENGINE_RESOURCE_NAME"]
# The agent's app directory (matches agent_directory in agents-cli-manifest.yaml).
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "wanderlust_planner")
# Location is embedded in the resource name: projects/<p>/locations/<loc>/reasoningEngines/<id>.
LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]

# A2A endpoint for an Agent Runtime deployment, via the Agent Engine HTTP
# passthrough. The card lives at the well-known path under this base.
A2A_BASE = (
    f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
    f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
)
A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"

# The agent tags its A2UI data parts with this mime type.
_A2UI_MIME = "application/json+a2ui"

# One set of ADC credentials, refreshed per request (access tokens expire ~1h).
_creds, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)


def _auth_headers() -> dict[str, str]:
    _creds.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_creds.token}",
        "Content-Type": "application/json",
    }


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    # Always return JSON so the browser never receives a plain-text 500 page
    # (which shows up in the chat as "Unexpected token 'I', "Internal S"... is
    # not valid JSON"). Any server-side failure now surfaces as a readable
    # message in the chat bubble instead.
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


# Reuse ONE A2A context per user so the agent remembers the conversation.
_contexts: dict[str, str] = {}
# Cache the agent card after the first fetch.
_card: AgentCard | None = None


async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        data = resp.json()
        
        # in older SDKs the url was at the top level
        # in 1.1.5 the url needs to be in supported_interfaces
        # We rewrite the JSON to ensure it matches what 1.1.5 expects
        
        # Make sure supported_interfaces is correctly formatted for 1.1.5
        # The agent engine adapter currently returns "additionalInterfaces" instead of "supportedInterfaces"
        # and has "preferredTransport". We need to map this to "supported_interfaces"
        
        supported_interfaces = []
        
        # In a2a-sdk v0.3 it used "url" and "preferredTransport" at root, and "additionalInterfaces".
        # a2a-sdk v1.x expects "supportedInterfaces" array with {"protocolBinding": "JSONRPC", "url": "..."}
        if "url" in data:
            transport = data.get("preferredTransport", "JSONRPC")
            supported_interfaces.append({"protocolBinding": transport, "url": A2A_BASE})
            
        for interface in data.get("additionalInterfaces", []):
            transport = interface.get("transport", "JSONRPC")
            # Override URL to A2A_BASE since we hit the runtime through a proxy
            supported_interfaces.append({"protocolBinding": transport, "url": A2A_BASE})
            
        data["supportedInterfaces"] = supported_interfaces
        
        if "additionalInterfaces" in data:
            del data["additionalInterfaces"]
        if "preferredTransport" in data:
            del data["preferredTransport"]
        if "url" in data:
            del data["url"]
        if "schema" in data:
            del data["schema"]
        
        from google.protobuf import json_format
        card = AgentCard()
        json_format.ParseDict(data, card, ignore_unknown_fields=True)
        
        _card = card
    return _card


def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        kind = p.WhichOneof("content") if hasattr(p, "WhichOneof") else None
        if kind == "text" and p.text:
            out.append({"kind": "text", "text": p.text})
        elif kind == "data":
            data_dict = {}
            if hasattr(p.data, "DESCRIPTOR"):
                try:
                    from google.protobuf import json_format
                    data_dict = json_format.MessageToDict(p.data)
                except Exception:
                    pass
            elif isinstance(p.data, dict):
                data_dict = p.data

            # Check for metadata inside data_dict or p.metadata
            meta = data_dict.get("metadata") if isinstance(data_dict, dict) else {}
            mime = meta.get("mimeType") or meta.get("mime_type") if isinstance(meta, dict) else None
            
            if not mime and hasattr(p, "metadata") and p.metadata:
                try:
                    from google.protobuf import json_format
                    p_meta = json_format.MessageToDict(p.metadata)
                    if isinstance(p_meta, dict):
                        mime = p_meta.get("mimeType") or p_meta.get("mime_type")
                except Exception:
                    pass

            if mime == _A2UI_MIME:
                card_payload = data_dict.get("message") or data_dict.get("data") or data_dict
                out.append({"kind": "a2ui", "data": card_payload})
        elif kind == "url":
            out.append({"kind": "image", "uri": p.url})
        else:
            root = getattr(p, "root", p)
            if hasattr(root, "text") and root.text:
                out.append({"kind": "text", "text": root.text})
    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
        card = await _get_card(client)
        factory = ClientFactory(
            ClientConfig(
                httpx_client=client,
            )
        )
        a2a_client = factory.create(card)

        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=message)],
        )
        if _contexts.get(user_id):
            msg.context_id = _contexts.get(user_id)

        req = SendMessageRequest(message=msg)

        last_task = None
        got_artifact_update = False
        async for response in a2a_client.send_message(req):
            if response.HasField("status_update") and response.status_update.status.HasField("message"):
                parts.extend(_extract_parts(response.status_update.status.message.parts))

        # Non-streaming fallback: pull parts from the final task's artifacts.
        if not got_artifact_update and last_task is not None:
            for artifact in getattr(last_task, "artifacts", None) or []:
                parts.extend(_extract_parts(artifact.parts))

    if not parts:
        # The turn produced no text or UI (e.g. the agent only ran tools, or a
        # tool stalled). Be honest rather than silent.
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


# Serve the chat UI (keep this mount last so /chat wins).
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
