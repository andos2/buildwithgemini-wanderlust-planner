from google.protobuf import json_format

def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        kind = p.WhichOneof("content") if hasattr(p, "WhichOneof") else None
        if kind == "text" and p.text:
            out.append({"kind": "text", "text": p.text})
        elif kind == "data":
            meta = {}
            if hasattr(p, "metadata") and p.metadata:
                try:
                    meta = json_format.MessageToDict(p.metadata)
                except Exception:
                    meta = dict(p.metadata) if hasattr(p.metadata, "items") else {}
            
            mime = meta.get("mimeType") or meta.get("mime_type") or meta.get("mimetype")
            if mime == _A2UI_MIME:
                data_val = p.data
                if hasattr(p.data, "DESCRIPTOR"):
                    try:
                        data_val = json_format.MessageToDict(p.data)
                    except Exception:
                        pass
                out.append({"kind": "a2ui", "data": data_val})
        elif kind == "url":
            out.append({"kind": "image", "uri": p.url})
        else:
            root = getattr(p, "root", p)
            if hasattr(root, "text") and root.text:
                out.append({"kind": "text", "text": root.text})
    return out
