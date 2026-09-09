def conflict(entity_id,
            left_version,right_version,
            left_state,right_state):
    return {"entity_id":entity_id,
            "left_version":left_version,
            "right_version":right_version,
            "left_state":left_state,
            "right_state":right_state,
            "status":"OPEN"}

def resolve(record,resolved_state,
            strategy):
    out=dict(record)
    out["resolved_state"]=resolved_state
    out["strategy"]=strategy
    out["status"]="RESOLVED"
    return out
