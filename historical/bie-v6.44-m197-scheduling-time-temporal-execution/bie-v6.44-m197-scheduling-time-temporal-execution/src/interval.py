def interval(every, unit="SECONDS", count=None):
    if every <= 0:
        raise ValueError("INVALID_INTERVAL")
    if unit not in {"SECONDS","MINUTES","HOURS","DAYS"}:
        raise ValueError("INVALID_INTERVAL_UNIT")
    return {"every":every,"unit":unit,"count":count}

def finite(record):
    return record["count"] is not None
