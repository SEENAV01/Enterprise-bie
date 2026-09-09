def secret_reference(secret_id,version=None,
                    service=None,scope=None):
    return {"secret_id":secret_id,"version":version,
            "service":service,"scope":scope,
            "reference_only":True}

def redact(value):
    return "[REDACTED]" if value is not None else None
