def projection(fields=None):
    return {"fields":fields or ["*"]}

def includes(record, field):
    return "*" in record["fields"] or field in record["fields"]
