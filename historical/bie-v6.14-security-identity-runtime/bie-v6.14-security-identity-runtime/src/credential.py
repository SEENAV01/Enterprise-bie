def credential(credential_id,
               kind,version,
               expires_at=None,status="ACTIVE"):
    return {"credential_id":credential_id,
            "kind":kind,"version":version,
            "expires_at":expires_at,
            "status":status}

def expired(record,now):
    return (record["expires_at"] is not None and
            now>=record["expires_at"])
