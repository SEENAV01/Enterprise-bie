def compatibility_rule(mode, required_fields=None,
                       allow_additive=True):
    if mode not in {"NONE","BACKWARD","FORWARD","FULL"}:
        raise ValueError("INVALID_COMPATIBILITY")
    return {"mode":mode,"required_fields":required_fields or [],
            "allow_additive":allow_additive}

def compatible(rule, old_fields, new_fields):
    if rule["mode"]=="NONE":
        return True
    old=set(old_fields); new=set(new_fields)
    if rule["mode"] in {"BACKWARD","FULL"} and not old.issubset(new):
        return False
    if rule["mode"] in {"FORWARD","FULL"} and not new.issubset(old):
        return False
    return True
