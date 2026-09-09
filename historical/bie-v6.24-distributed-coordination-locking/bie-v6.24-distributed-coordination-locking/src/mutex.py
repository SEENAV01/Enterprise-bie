def mutex(resource_id,
          owner=None,
          mode="EXCLUSIVE"):
    if mode not in {"EXCLUSIVE","SHARED"}:
        raise ValueError("INVALID_MUTEX_MODE")
    return {"resource_id":resource_id,
            "owner":owner,
            "mode":mode,
            "status":"FREE" if owner is None else "HELD"}

def acquirable(record):
    return record["status"]=="FREE"
