def alert_rule(rule_id,name,
               condition,severity="WARNING",
               for_seconds=0):
    return {"rule_id":rule_id,"name":name,
            "condition":condition,
            "severity":severity,
            "for_seconds":for_seconds}

def evaluate(rule,observed):
    return bool(observed.get(rule["condition"],False))
