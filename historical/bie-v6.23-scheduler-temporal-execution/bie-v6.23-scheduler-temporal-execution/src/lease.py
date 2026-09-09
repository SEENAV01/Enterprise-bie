def execution_lease(execution_id,
                    owner,
                    expires_at):
    return {"execution_id":execution_id,
            "owner":owner,
            "expires_at":expires_at,
            "status":"HELD"}

def valid(record,now):
    return record["status"]=="HELD" and now < record["expires_at"]

def release(record):
    out=dict(record); out["status"]="RELEASED"; return out
