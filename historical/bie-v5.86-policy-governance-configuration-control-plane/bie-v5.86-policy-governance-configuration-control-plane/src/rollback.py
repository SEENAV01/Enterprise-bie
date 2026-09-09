def rollback_record(policy_id,current_version,
                   target_version,reason,operator):
    return {"policy_id":policy_id,
            "current_version":current_version,
            "target_version":target_version,
            "reason":reason,"operator":operator,
            "status":"REQUESTED"}

def execute_rollback(record):
    out=dict(record); out["status"]="EXECUTED"; return out
