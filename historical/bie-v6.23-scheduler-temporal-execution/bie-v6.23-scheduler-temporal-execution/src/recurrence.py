def recurrence(frequency,
                interval=1,
                count=None,
                until=None):
    if frequency not in {"ONCE","MINUTELY","HOURLY",
                         "DAILY","WEEKLY","MONTHLY"}:
        raise ValueError("INVALID_FREQUENCY")
    if interval < 1:
        raise ValueError("INVALID_INTERVAL")
    return {"frequency":frequency,
            "interval":interval,
            "count":count,
            "until":until}

def bounded(record):
    return record["count"] is not None or record["until"] is not None
