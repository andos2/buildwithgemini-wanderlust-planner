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
            data_dict = {}
            if hasattr(p.data, "DESCRIPTOR"):
                try:
                    from google.protobuf import json_format
                    data_dict = json_format.MessageToDict(p.data)
                except Exception:
                    pass
            elif isinstance(p.data, dict):
                data_dict = p.data

            # Check for metadata inside data_dict or p.metadata
            meta = data_dict.get("metadata") if isinstance(data_dict, dict) else {}
            mime = meta.get("mimeType") or meta.get("mime_type") if isinstance(meta, dict) else None
            
            if not mime and hasattr(p, "metadata") and p.metadata:
                try:
                    from google.protobuf import json_format
                    p_meta = json_format.MessageToDict(p.metadata)
                    if isinstance(p_meta, dict):
                        mime = p_meta.get("mimeType") or p_meta.get("mime_type")
                except Exception:
                    pass

            if mime == _A2UI_MIME:
                card_payload = data_dict.get("message") or data_dict.get("data") or data_dict
                out.append({"kind": "a2ui", "data": card_payload})
        elif kind == "url":
            out.append({"kind": "image", "uri": p.url})
        else:
            root = getattr(p, "root", p)
            if hasattr(root, "text") and root.text:
                out.append({"kind": "text", "text": root.text})
    return out"""

content = re.sub(r'def _extract_parts\(parts: list\) -> list\[dict\]:.*?return out', new_extract, content, flags=re.DOTALL)

with open("frontend/main.py", "w") as f:
    f.write(content)
