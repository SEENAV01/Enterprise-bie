def policy(name,effect="ALLOW",
           conditions=None,priority=0):
    if effect not in {"ALLOW","DENY"}:
        raise ValueError("INVALID_POLICY_EFFECT")
    return {"name":name,"effect":effect,
            "conditions":conditions or {},
            "priority":priority}

def evaluate(record,context):
    return record["effect"]=="ALLOW"
