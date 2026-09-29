import re

with open("frontend/main.py", "r") as f:
    content = f.read()

debug_loop = """        async for response in a2a_client.send_message(req):
            print("RESP HAS STATUS_UPDATE?", response.HasField("status_update"))
            if response.HasField("status_update"):
                print("STATUS MSG:", response.status_update.status.message)
                print("STATUS PARTS:", response.status_update.status.message.parts)
                extracted = _extract_parts(response.status_update.status.message.parts)
                print("EXTRACTED:", extracted)
                parts.extend(extracted)
            if response.HasField("artifact_update"):
                parts.extend(_extract_parts(response.artifact_update.artifact.parts))"""

content = re.sub(r'        async for response in a2a_client\.send_message\(req\):.*?parts\.extend\(_extract_parts\(response\.artifact_update\.artifact\.parts\)\)', debug_loop, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
