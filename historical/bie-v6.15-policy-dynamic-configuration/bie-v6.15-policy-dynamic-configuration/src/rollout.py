def rollout(config_version,
            strategy="CANARY",
            percentage=0):
    if strategy not in {"ALL_AT_ONCE",
                        "CANARY","PROGRESSIVE"}:
        raise ValueError("INVALID_ROLLOUT_STRATEGY")
    return {"config_version":config_version,
            "strategy":strategy,
            "percentage":percentage,
            "status":"PLANNED"}

def advance(record,percentage):
    out=dict(record)
    out["percentage"]=percentage
    out["status"]="ACTIVE" if percentage>0 else "PLANNED"
    return out
