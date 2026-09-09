def object_version(version_id,
                  created_at,
                  is_current=False):
    return {"version_id":version_id,
            "created_at":created_at,
            "is_current":is_current}

def current(record):
    return record["is_current"]
