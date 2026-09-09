def timer(timer_id, target_ref,
         fire_at, timezone="UTC"):
    return {"timer_id":timer_id,
            "target_ref":target_ref,
            "fire_at":fire_at,
            "timezone":timezone,
            "status":"SCHEDULED"}

def due(record,now):
    return now >= record["fire_at"]
