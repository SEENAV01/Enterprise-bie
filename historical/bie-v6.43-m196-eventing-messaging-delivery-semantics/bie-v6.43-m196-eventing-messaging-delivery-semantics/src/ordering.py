def ordering(mode="PARTITION", key=None):
    if mode not in {"NONE","PARTITION","GLOBAL","KEY"}:
        raise ValueError("INVALID_ORDERING_MODE")
    return {"mode":mode,"key":key}

def ordered(record):
    return record["mode"]!="NONE"
