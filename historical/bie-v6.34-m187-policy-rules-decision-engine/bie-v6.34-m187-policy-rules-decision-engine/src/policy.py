def policy(policy_id, rules, version=1, mode="ALL"):
    if mode not in {"ALL","FIRST_MATCH","BEST_MATCH"}:
        raise ValueError("INVALID_POLICY_MODE")
    return {"policy_id":policy_id,"rules":rules,
            "version":version,"mode":mode,"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
