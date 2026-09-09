def consistency(mode="EVENTUAL", max_staleness_ms=None):
    if mode not in {"EVENTUAL","SESSION","BOUNDED","STRONG"}:
        raise ValueError("INVALID_CONSISTENCY")
    return {"mode":mode,"max_staleness_ms":max_staleness_ms}

def strong(record):
    return record["mode"]=="STRONG"
