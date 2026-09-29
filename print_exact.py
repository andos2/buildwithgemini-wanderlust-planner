import re

with open("frontend/main.py", "r") as f:
    content = f.read()

debug_loop = """        async for response in a2a_client.send_message(req):
            if response.HasField("status_update") and response.status_update.status.HasField("message"):
                for p in response.status_update.status.message.parts:
                    print("PART REPR:", repr(p))
                    print("PART WHICH:", p.WhichOneof("data"))
                parts.extend(_extract_parts(response.status_update.status.message.parts))"""

content = re.sub(r'        async for response in a2a_client\.send_message\(req\):.*?parts\.extend\(_extract_parts\(response\.artifact_update\.artifact\.parts\)\)', debug_loop, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
