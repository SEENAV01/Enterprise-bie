def facet(field,
          limit=10,
          sort="COUNT_DESC"):
    if sort not in {"COUNT_DESC","VALUE_ASC"}:
        raise ValueError("INVALID_FACET_SORT")
    return {"field":field,
            "limit":limit,
            "sort":sort}

def count(values):
    out={}
    for value in values:
        out[value]=out.get(value,0)+1
    return out
