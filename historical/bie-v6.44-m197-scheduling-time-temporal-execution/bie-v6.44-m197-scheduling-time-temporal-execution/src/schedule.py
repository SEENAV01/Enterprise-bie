def schedule(schedule_id, start_at=None, end_at=None,
             recurrence=None, timezone="UTC"):
    return {"schedule_id":schedule_id,"start_at":start_at,
            "end_at":end_at,"recurrence":recurrence,
            "timezone":timezone,"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
