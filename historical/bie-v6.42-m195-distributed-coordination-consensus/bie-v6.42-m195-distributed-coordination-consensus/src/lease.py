def lease(lease_id, holder, expires_at,
         renewable=True):
    return {"lease_id":lease_id,"holder":holder,
            "expires_at":expires_at,"renewable":renewable,
            "status":"ACTIVE"}

def held_by(record, holder):
    return record["holder"]==holder and record["status"]=="ACTIVE"
