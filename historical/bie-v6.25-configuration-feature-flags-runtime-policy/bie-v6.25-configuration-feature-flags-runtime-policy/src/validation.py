def rule(key,required=False,
         allowed=None,min_value=None,max_value=None):
    return {"key":key,"required":required,
            "allowed":allowed,
            "min_value":min_value,
            "max_value":max_value}

def validate(value,r):
    if value is None:
        return not r["required"]
    if r["allowed"] is not None and value not in r["allowed"]:
        return False
    if r["min_value"] is not None and value < r["min_value"]:
        return False
    if r["max_value"] is not None and value > r["max_value"]:
        return False
    return True
