def filter_expression(field,
                     operator,value):
    if operator not in {"EQ","NE","GT","GTE",
                        "LT","LTE","IN","PREFIX"}:
        raise ValueError("INVALID_FILTER_OPERATOR")
    return {"field":field,
            "operator":operator,
            "value":value}

def matches(expr,record):
    op=expr["operator"]
    left=record.get(expr["field"])
    right=expr["value"]
    if op=="EQ": return left==right
    if op=="NE": return left!=right
    if op=="GT": return left is not None and left>right
    if op=="GTE": return left is not None and left>=right
    if op=="LT": return left is not None and left<right
    if op=="LTE": return left is not None and left<=right
    if op=="IN": return left in right
    if op=="PREFIX": return isinstance(left,str) and left.startswith(right)
    return False
