def object_version(object_id,
                  version_id,
                  previous=None,
                  is_current=False):
    return {"object_id":object_id,
            "version_id":version_id,
            "previous":previous,
            "is_current":is_current}

def current(record):
    return record["is_current"]
