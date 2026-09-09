def governance_rule(rule_id, scope,
                    requirement, severity="MEDIUM"):
    if severity not in {"LOW","MEDIUM","HIGH","CRITICAL"}:
        raise ValueError("INVALID_SEVERITY")
    return {"rule_id":rule_id,"scope":scope,
            "requirement":requirement,"severity":severity}

def applies(record,scope):
    return record["scope"]==scope or record["scope"]=="*"
