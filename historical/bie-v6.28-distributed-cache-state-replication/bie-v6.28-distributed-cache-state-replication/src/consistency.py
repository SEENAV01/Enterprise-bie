def consistency_mode(mode="EVENTUAL",
                    max_staleness_seconds=None):
    if mode not in {"EVENTUAL","READ_YOUR_WRITES",
                    "BOUNDED_STALENESS","STRONG"}:
        raise ValueError("INVALID_CONSISTENCY_MODE")
    return {"mode":mode,
            "max_staleness_seconds":max_staleness_seconds}

def permits_stale(record,staleness):
    if record["mode"]=="STRONG":
        return staleness==0
    if record["max_staleness_seconds"] is None:
        return True
    return staleness <= record["max_staleness_seconds"]
