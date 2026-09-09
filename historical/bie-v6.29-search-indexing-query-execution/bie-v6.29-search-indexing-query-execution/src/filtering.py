def filter_clause(field,operator,value):
    if operator not in {"EQ","NE","GT","GTE","LT","LTE","IN","PREFIX"}:
        raise ValueError("INVALID_FILTER_OPERATOR")
    return {"field":field,"operator":operator,"value":value}

def matches(record,clause):
    value=record.get(clause["field"])
    op=clause["operator"]; target=clause["value"]
    if op=="EQ": return value==target
    if op=="NE": return value!=target
    if op=="GT": return value is not None and value>target
    if op=="GTE": return value is not None and value>=target
    if op=="LT": return value is not None and value<target
    if op=="LTE": return value is not None and value<=target
    if op=="IN": return value in target
    if op=="PREFIX": return isinstance(value,str) and value.startswith(target)
    return False
