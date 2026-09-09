def key_version(key_id, version, created_at=None,
                expires_at=None, status="ACTIVE"):
    return {"key_id":key_id,"version":version,
            "created_at":created_at,"expires_at":expires_at,
            "status":status}

def next_version(current):
    return current+1
