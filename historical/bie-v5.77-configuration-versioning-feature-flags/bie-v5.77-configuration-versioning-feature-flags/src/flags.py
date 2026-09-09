def feature_flag(name,enabled=False,default=False,
                rules=None):
    return {"name":name,"enabled":enabled,
            "default":default,"rules":rules or []}

def flag_value(flag,context=None):
    if not flag.get("enabled",False):
        return flag.get("default",False)
    for rule in flag.get("rules",[]):
        if all(context.get(k)==v for k,v in rule.get("when",{}).items()):
            return rule.get("value",flag.get("default",False))
    return flag.get("default",False)
