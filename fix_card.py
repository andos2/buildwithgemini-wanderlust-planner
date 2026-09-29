import re

with open("frontend/main.py", "r") as f:
    content = f.read()

# Fix agent card loading logic in proxy to handle extra fields from old runtime returning to new SDK
new_get_card = """async def _get_card(client: httpx.AsyncClient) -> AgentCard:
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        data = resp.json()
        if "supportedInterfaces" in data:
            del data["supportedInterfaces"]
        if "description" in data:
            del data["description"]
        if "schema" in data:
            del data["schema"]
        
        # a2a-sdk 1.x strict protobuf parsing fails on unknown fields
        from google.protobuf import json_format
        card = AgentCard()
        json_format.ParseDict(data, card, ignore_unknown_fields=True)
        
        # Agent Runtime does not serve a public card URL, so point the client at
        # the passthrough base for message sends.
        card.url = A2A_BASE
        _card = card
    return _card"""

content = re.sub(r'async def _get_card.*?return _card', new_get_card, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
