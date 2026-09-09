def result(items=None, next_cursor=None,
           total=None, partial=False):
    return {"items":items or [],"next_cursor":next_cursor,
            "total":total,"partial":partial}

def complete(record):
    return not record["partial"]
