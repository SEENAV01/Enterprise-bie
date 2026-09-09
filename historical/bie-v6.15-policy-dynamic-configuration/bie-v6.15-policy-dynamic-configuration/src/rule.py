def rule(rule_id,condition,effect,
         priority=0,scope=None):
    if effect not in {"ALLOW","DENY","SET","UNSET"}:
        raise ValueError("INVALID_RULE_EFFECT")
    return {"rule_id":rule_id,
            "condition":condition,
            "effect":effect,
            "priority":priority,
            "scope":scope}

def matches(record,context):
    return record["condition"] == context
