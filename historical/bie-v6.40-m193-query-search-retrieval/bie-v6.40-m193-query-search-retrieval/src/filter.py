def predicate(field, operator, value):
    allowed={"EQ","NE","GT","GTE","LT","LTE","IN","CONTAINS","PREFIX"}
    if operator not in allowed:
        raise ValueError("INVALID_FILTER_OPERATOR")
    return {"field":field,"operator":operator,"value":value}

def matches(record, value):
    op=record["operator"]; target=record["value"]
    if op=="EQ": return value==target
    if op=="NE": return value!=target
    if op=="GT": return value>target
    if op=="GTE": return value>=target
    if op=="LT": return value<target
    if op=="LTE": return value<=target
    if op=="IN": return value in target
    if op=="CONTAINS": return target in value
    if op=="PREFIX": return str(value).startswith(str(target))
    return False
