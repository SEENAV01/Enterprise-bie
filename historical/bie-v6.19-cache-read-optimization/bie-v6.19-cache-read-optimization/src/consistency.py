def consistency_mode(cache,
                    mode="EVENTUAL"):
    if mode not in {"EVENTUAL","READ_YOUR_WRITES",
                    "STRONG"}:
        raise ValueError("INVALID_CACHE_CONSISTENCY")
    return {"cache":cache,"mode":mode}

def acceptable(record,allowed):
    return record["mode"] in allowed
