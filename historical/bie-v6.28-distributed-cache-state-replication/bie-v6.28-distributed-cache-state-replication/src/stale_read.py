def stale_read_policy(allow=True,
                     max_staleness_seconds=None):
    if max_staleness_seconds is not None and max_staleness_seconds < 0:
        raise ValueError("INVALID_STALENESS")
    return {"allow":allow,
            "max_staleness_seconds":max_staleness_seconds}

def allowed(record,staleness):
    if not record["allow"]:
        return staleness==0
    if record["max_staleness_seconds"] is None:
        return True
    return staleness <= record["max_staleness_seconds"]
