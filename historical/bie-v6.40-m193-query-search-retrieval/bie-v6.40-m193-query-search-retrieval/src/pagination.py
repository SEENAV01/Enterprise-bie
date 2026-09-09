def page(limit=50, cursor=None, offset=None):
    if limit<1:
        raise ValueError("INVALID_PAGE_LIMIT")
    if cursor is not None and offset is not None:
        raise ValueError("CURSOR_OFFSET_CONFLICT")
    return {"limit":limit,"cursor":cursor,"offset":offset}

def has_cursor(record):
    return record["cursor"] is not None
