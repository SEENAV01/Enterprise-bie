def consistency(mode="EVENTUAL", timeout_ms=None):
    if mode not in {"EVENTUAL","SESSION","BOUNDED","STRONG"}:
        raise ValueError("INVALID_CONSISTENCY")
    return {"mode":mode,"timeout_ms":timeout_ms}

def strong(record):
    return record["mode"]=="STRONG"
