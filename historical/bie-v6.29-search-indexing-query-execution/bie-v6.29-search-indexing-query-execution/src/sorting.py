def sort_clause(field,direction="ASC"):
    if direction not in {"ASC","DESC"}:
        raise ValueError("INVALID_SORT_DIRECTION")
    return {"field":field,"direction":direction}

def key(record,clause):
    return record.get(clause["field"])
