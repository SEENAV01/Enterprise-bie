def timer(timer_id,workflow_id,
         fire_at,reason=None):
    return {"timer_id":timer_id,
            "workflow_id":workflow_id,
            "fire_at":fire_at,
            "reason":reason,
            "status":"SCHEDULED"}

def fire(record,now):
    if now < record["fire_at"]:
        return dict(record)
    out=dict(record); out["status"]="FIRED"; return out
