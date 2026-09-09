def idempotency_key(key, request_hash,
                    ttl_seconds=None):
    return {"key":key,"request_hash":request_hash,
            "ttl_seconds":ttl_seconds,"status":"NEW"}

def duplicate(existing, request_hash):
    return existing is not None and existing["request_hash"]==request_hash
