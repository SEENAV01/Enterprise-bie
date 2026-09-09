def lock_request(lock_id,resource,
                owner,ttl_seconds,requested_at):
    return {"lock_id":lock_id,"resource":resource,
            "owner":owner,"ttl_seconds":ttl_seconds,
            "requested_at":requested_at}

def lock_record(lock_id,resource,owner,
                token,expires_at,status="HELD"):
    return {"lock_id":lock_id,"resource":resource,
            "owner":owner,"fencing_token":token,
            "expires_at":expires_at,"status":status}

def valid_owner(lock,owner,now):
    return (lock.get("owner")==owner and
            lock.get("status")=="HELD" and
            now < lock.get("expires_at",0))
