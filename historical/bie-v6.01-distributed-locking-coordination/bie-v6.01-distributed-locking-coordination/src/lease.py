def lease(lease_id,owner,issued_at,
          expires_at,renewable=True):
    return {"lease_id":lease_id,"owner":owner,
            "issued_at":issued_at,"expires_at":expires_at,
            "renewable":renewable,"status":"ACTIVE"}

def active(lease_record,now):
    return (lease_record.get("status")=="ACTIVE" and
            now < lease_record.get("expires_at",0))

def expire(lease_record):
    out=dict(lease_record); out["status"]="EXPIRED"
    return out
