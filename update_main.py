import re

with open("frontend/main.py", "r") as f:
    content = f.read()

# Update imports for 1.1.5
imports = """from a2a.client import ClientConfig, ClientFactory
from a2a.types import (
    AgentCard,
    Message,
    Part,
    SendMessageRequest,
)"""

content = re.sub(r'from a2a\.client import ClientConfig, ClientFactory\nfrom a2a\.types import \(.*?\)', imports, content, flags=re.DOTALL)

# Update chat endpoint logic
new_chat_loop = """        req = SendMessageRequest(message=Message(parts=[Part(text=message)]))
        if _contexts.get(user_id):
            req.message.context_id = _contexts.get(user_id)

        last_task = None
        got_artifact_update = False
        async for response in a2a_client.send_message(req):
            if response.HasField("task"):
                last_task = response.task
                if response.task.context_id:
                    _contexts[user_id] = response.task.context_id
            if response.HasField("artifact_update"):
                got_artifact_update = True
                parts.extend(_extract_parts(response.artifact_update.artifact.parts))

        # Non-streaming fallback: pull parts from the final task's artifacts.
        if not got_artifact_update and last_task is not None:
            for artifact in getattr(last_task, "artifacts", None) or []:
                parts.extend(_extract_parts(artifact.parts))"""

content = re.sub(r'        if hasattr\(Part, "HasField"\):.*?parts\.extend\(_extract_parts\(artifact\.parts\)\)', new_chat_loop, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
