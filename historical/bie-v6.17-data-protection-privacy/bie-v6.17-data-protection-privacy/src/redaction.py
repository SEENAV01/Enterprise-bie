def redaction(resource,
             fields,placeholder="[REDACTED]"):
    return {"resource":resource,
            "fields":fields,
            "placeholder":placeholder}

def redact(record,data):
    out=dict(data)
    for field in record["fields"]:
        if field in out:
            out[field]=record["placeholder"]
    return out
