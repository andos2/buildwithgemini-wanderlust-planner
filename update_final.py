import re

with open("frontend/main.py", "r") as f:
    content = f.read()

new_loop = """        async for response in a2a_client.send_message(req):
            if response.HasField("task"):
                last_task = response.task
                if response.task.context_id:
                    _contexts[user_id] = response.task.context_id
            if response.HasField("status_update") and response.status_update.status.HasField("message"):
                parts.extend(_extract_parts(response.status_update.status.message.parts))
            if response.HasField("artifact_update"):
                parts.extend(_extract_parts(response.artifact_update.artifact.parts))"""

content = re.sub(r'        async for response in a2a_client\.send_message\(req\):.*?parts\.extend\(_extract_parts\(response\.artifact_update\.artifact\.parts\)\)', new_loop, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
