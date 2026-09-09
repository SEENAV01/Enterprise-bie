def order(field, direction="ASC"):
    if direction not in {"ASC","DESC"}:
        raise ValueError("INVALID_SORT_DIRECTION")
    return {"field":field,"direction":direction}

def reverse(record):
    return record["direction"]=="DESC"
