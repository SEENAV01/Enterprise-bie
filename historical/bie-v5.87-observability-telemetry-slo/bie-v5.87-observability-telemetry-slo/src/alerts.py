def alert_rule(name,condition,severity="WARNING"):
    return {"name":name,"condition":condition,
            "severity":severity}

def evaluate(rule,metrics):
    condition=rule.get("condition")
    if callable(condition):
        fired=bool(condition(metrics))
    else:
        fired=False
    return {"rule":rule["name"],"fired":fired,
            "severity":rule["severity"]}
