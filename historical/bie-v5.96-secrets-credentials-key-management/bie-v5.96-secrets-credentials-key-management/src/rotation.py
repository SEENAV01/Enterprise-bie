def rotation_policy(secret_id,interval_seconds,
                     overlap_seconds=0):
    return {"secret_id":secret_id,
            "interval_seconds":interval_seconds,
            "overlap_seconds":overlap_seconds}

def rotation_due(last_rotated,now,policy):
    return now-last_rotated>=policy["interval_seconds"]
