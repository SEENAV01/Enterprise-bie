def condition(field, operator, expected):
    if operator not in {"EQ","NE","EXISTS","NOT_EXISTS"}:
        raise ValueError("INVALID_CONDITION")
    return {"field":field,"operator":operator,
            "expected":expected}

def evaluate(record, value=None):
    op=record["operator"]
    if op=="EQ": return value==record["expected"]
    if op=="NE": return value!=record["expected"]
    if op=="EXISTS": return value is not None
    if op=="NOT_EXISTS": return value is None
    return False
