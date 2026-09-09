def query_consistency(mode="EVENTUAL",
                     max_lag_seconds=None):
    if mode not in {"EVENTUAL","BOUNDED_STALENESS","STRONG"}:
        raise ValueError("INVALID_QUERY_CONSISTENCY")
    return {"mode":mode,
            "max_lag_seconds":max_lag_seconds}

def acceptable(record,lag_seconds):
    if record["mode"]=="STRONG":
        return lag_seconds==0
    if record["max_lag_seconds"] is None:
        return True
    return lag_seconds <= record["max_lag_seconds"]
