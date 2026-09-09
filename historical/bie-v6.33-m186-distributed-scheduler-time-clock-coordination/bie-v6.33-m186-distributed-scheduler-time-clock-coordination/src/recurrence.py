def recurrence(kind, interval=None,
                count=None, until=None):
    if kind not in {"CRON","INTERVAL","CALENDAR"}:
        raise ValueError("INVALID_RECURRENCE")
    return {"kind":kind,"interval":interval,
            "count":count,"until":until}

def bounded(record):
    return record["count"] is not None or record["until"] is not None
