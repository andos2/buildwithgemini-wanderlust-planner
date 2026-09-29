import re

with open("frontend/main.py", "r") as f:
    content = f.read()

# Add Role to imports
content = content.replace("SendMessageRequest,\n)", "SendMessageRequest,\n    Role,\n)")

new_req = """        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.ROLE_USER,
            parts=[Part(text=message)],
        )
        if _contexts.get(user_id):
            msg.context_id = _contexts.get(user_id)

        req = SendMessageRequest(message=msg)"""

content = re.sub(r'        req = SendMessageRequest\(message=Message\(parts=\[Part\(text=message\)\]\)\)\n        if _contexts\.get\(user_id\):\n            req\.message\.context_id = _contexts\.get\(user_id\)', new_req, content)

with open("frontend/main.py", "w") as f:
    f.write(content)
