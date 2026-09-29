import re

with open("frontend/main.py", "r") as f:
    content = f.read()

# Instead of setting card.url, we need to ensure card.supported_interfaces has the correct URL
new_get_card = """async def _get_card(client: httpx.AsyncClient) -> AgentCard:
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
    return _card"""

content = re.sub(r'async def _get_card.*?return _card', new_get_card, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
