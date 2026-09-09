def hold(hold_id,resource_id,
         reason,created_at,expires_at=None):
    return {"hold_id":hold_id,
            "resource_id":resource_id,
            "reason":reason,
            "created_at":created_at,
            "expires_at":expires_at,
            "status":"ACTIVE"}

def active(record,now):
    if record.get("status")!="ACTIVE":
        return False
    end=record.get("expires_at")
    return end is None or now < end
