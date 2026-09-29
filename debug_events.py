import re

with open("frontend/main.py", "r") as f:
    content = f.read()

debug_loop = """        async for response in a2a_client.send_message(req):
            print("RESPONSE:", response)
            if response.HasField("task"):
                last_task = response.task
                if response.task.context_id:
                    _contexts[user_id] = response.task.context_id
            if response.HasField("artifact_update"):
                got_artifact_update = True
                parts.extend(_extract_parts(response.artifact_update.artifact.parts))"""

content = re.sub(r'        async for response in a2a_client\.send_message\(req\):.*?parts\.extend\(_extract_parts\(response\.artifact_update\.artifact\.parts\)\)', debug_loop, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
