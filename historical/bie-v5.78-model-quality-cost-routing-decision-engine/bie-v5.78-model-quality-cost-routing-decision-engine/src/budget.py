def budget_policy(max_cost=None,hard=False):
    return {"max_cost":max_cost,"hard":hard}

def within_budget(model,policy):
    limit=policy.get("max_cost")
    if limit is None: return True
    return model.get("cost_per_unit",0)<=limit
