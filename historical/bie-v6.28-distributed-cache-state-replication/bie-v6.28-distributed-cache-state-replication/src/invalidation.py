def invalidation(key,
                   reason="EXPLICIT",
                   version=None):
    return {"key":key,"reason":reason,
            "version":version,
            "status":"REQUESTED"}

def apply(record):
    out=dict(record); out["status"]="INVALIDATED"; return out
