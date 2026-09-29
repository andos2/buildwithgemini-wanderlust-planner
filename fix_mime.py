import re

with open("frontend/main.py", "r") as f:
    content = f.read()

new_extract = """def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        kind = p.WhichOneof("content") if hasattr(p, "WhichOneof") else None
        if kind == "text" and p.text:
            out.append({"kind": "text", "text": p.text})
        elif kind == "data":
            meta = {}
            if hasattr(p, "metadata") and p.metadata:
                meta = dict(p.metadata)
            mime = meta.get("mimeType") or meta.get("mime_type")
            if mime == _A2UI_MIME:
                from google.protobuf import json_format
                data_val = json_format.MessageToDict(p.data) if hasattr(p.data, "DESCRIPTOR") else p.data
                out.append({"kind": "a2ui", "data": data_val})
        elif kind == "url":
            out.append({"kind": "image", "uri": p.url})
        else:
            # Fallback for older non-protobuf objects
            root = getattr(p, "root", p)
            if hasattr(root, "text") and root.text:
                out.append({"kind": "text", "text": root.text})
    return out"""

content = re.sub(r'def _extract_parts\(parts: list\) -> list\[dict\]:.*?return out', new_extract, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
