import re

with open("frontend/main.py", "r") as f:
    content = f.read()

new_extract = """def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        if hasattr(p, "HasField"):
            if p.HasField("text") and p.text:
                out.append({"kind": "text", "text": p.text})
            elif p.HasField("data"):
                mime = None
                if hasattr(p, "metadata") and p.metadata:
                    mime = dict(p.metadata).get("mimeType")
                if mime == "application/json+a2ui":
                    out.append({"kind": "a2ui", "data": p.data.decode("utf-8") if isinstance(p.data, bytes) else p.data})
            elif p.HasField("file"):
                uri = getattr(p.file, "uri", None)
                if uri:
                    out.append({"kind": "image", "uri": uri})
        else:
            # fallback for older sdk
            root = getattr(p, "root", p)
            if hasattr(root, "text") and root.text:
                out.append({"kind": "text", "text": root.text})
            elif getattr(root, "data", None) is not None:
                meta = getattr(root, "metadata", None) or {}
                mime = meta.get("mimeType") if isinstance(meta, dict) else None
                if mime == "application/json+a2ui":
                    out.append({"kind": "a2ui", "data": root.data})
            elif hasattr(root, "file"):
                uri = getattr(getattr(root, "file", None), "uri", None)
                if uri:
                    out.append({"kind": "image", "uri": uri})
    return out"""

content = re.sub(r'def _extract_parts\(parts: list\) -> list\[dict\]:.*?return out', new_extract, content, flags=re.DOTALL)

# update message creation for 1.x
new_msg = """        if hasattr(Part, "HasField"): # a2a-sdk 1.x
            msg = Message(
                message_id=str(uuid.uuid4()),
                parts=[Part(text=message)],
            )
            # 1.x doesn't use context_id directly on Message initialization in the same way, or uses author/context_id properties
        else:
            msg = Message(
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=[Part(root=TextPart(text=message))],
                context_id=_contexts.get(user_id),
            )"""

content = re.sub(r'        msg = Message\(.*?context_id=_contexts\.get\(user_id\),\n        \)', new_msg, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
