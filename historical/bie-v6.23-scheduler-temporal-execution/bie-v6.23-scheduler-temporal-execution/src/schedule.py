def schedule(schedule_id, target_ref,
             start_at=None, timezone="UTC",
             enabled=True):
    return {"schedule_id":schedule_id,
            "target_ref":target_ref,
            "start_at":start_at,
            "timezone":timezone,
            "enabled":enabled}

def active(record):
    return record["enabled"]
