def override(policy_id, target, value, reason,
             actor, expires_at=None):
    return {"policy_id":policy_id,"target":target,"value":value,
            "reason":reason,"actor":actor,
            "expires_at":expires_at,"status":"ACTIVE"}

def active(record, now=None):
    return record["status"]=="ACTIVE"
