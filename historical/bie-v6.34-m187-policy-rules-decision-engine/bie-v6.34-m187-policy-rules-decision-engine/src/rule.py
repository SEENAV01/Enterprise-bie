def rule(rule_id, predicate, effect, priority=0, version=1):
    if not rule_id or not predicate or not effect:
        raise ValueError("INVALID_RULE")
    return {"rule_id":rule_id,"predicate":predicate,"effect":effect,
            "priority":priority,"version":version,"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
