def schedule(schedule_id, expression, timezone="UTC",
             start=None, end=None):
    if not schedule_id or not expression:
        raise ValueError("INVALID_SCHEDULE")
    return {"schedule_id":schedule_id,"expression":expression,
            "timezone":timezone,"start":start,"end":end,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
