def responsive_rule(object_id,condition,action,value=None):
    return {"object_id":object_id,"condition":condition,
            "action":action,"value":value}

def responsive_plan(rules,breakpoints=None):
    return {"breakpoints":breakpoints or [],
            "rules":rules}
