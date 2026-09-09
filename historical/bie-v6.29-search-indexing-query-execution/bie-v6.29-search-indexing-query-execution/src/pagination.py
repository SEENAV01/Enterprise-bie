def pagination(limit=20,
               cursor=None,
               offset=None):
    if limit < 1:
        raise ValueError("INVALID_LIMIT")
    if cursor is not None and offset is not None:
        raise ValueError("CURSOR_AND_OFFSET_CONFLICT")
    return {"limit":limit,
            "cursor":cursor,
            "offset":offset}

def bounded(record,max_limit=100):
    return record["limit"] <= max_limit
