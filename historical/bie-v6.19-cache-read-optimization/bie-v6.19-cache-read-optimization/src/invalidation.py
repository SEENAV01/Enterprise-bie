def invalidation(key,
                  reason,
                  mode="EXACT"):
    if mode not in {"EXACT","PREFIX","TAG"}:
        raise ValueError("INVALID_INVALIDATION_MODE")
    return {"key":key,"reason":reason,
            "mode":mode,"status":"REQUESTED"}

def complete(record):
    out=dict(record); out["status"]="COMPLETED"; return out
