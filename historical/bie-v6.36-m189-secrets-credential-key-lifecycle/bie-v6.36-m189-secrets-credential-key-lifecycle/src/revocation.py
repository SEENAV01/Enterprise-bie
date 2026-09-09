def revocation(key_id, version, reason,
               revoked_at=None):
    return {"key_id":key_id,"version":version,
            "reason":reason,"revoked_at":revoked_at,
            "status":"REVOKED"}

def revoked(record):
    return record["status"]=="REVOKED"
