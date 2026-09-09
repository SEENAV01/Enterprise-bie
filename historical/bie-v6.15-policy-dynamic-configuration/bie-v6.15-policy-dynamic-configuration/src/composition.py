def compose(rule_ids,
             operator="AND"):
    if operator not in {"AND","OR"}:
        raise ValueError("INVALID_RULE_OPERATOR")
    return {"rule_ids":rule_ids,
            "operator":operator}

def empty(record):
    return len(record["rule_ids"])==0
