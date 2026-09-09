def retrieval_consistency(mode="EVENTUAL"):
    if mode not in {"EVENTUAL","SESSION","STRONG"}:
        raise ValueError("INVALID_RETRIEVAL_CONSISTENCY")
    return {"mode":mode}

def acceptable(record,allowed):
    return record["mode"] in allowed
