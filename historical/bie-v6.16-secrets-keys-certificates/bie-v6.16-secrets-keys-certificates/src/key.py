def key_metadata(key_id,version,
                algorithm,usage,
                status="ACTIVE",
                created_at=None,
                expires_at=None):
    return {"key_id":key_id,
            "version":version,
            "algorithm":algorithm,
            "usage":usage,
            "status":status,
            "created_at":created_at,
            "expires_at":expires_at}

def usable(record,now=None):
    if record["status"]!="ACTIVE":
        return False
    return record["expires_at"] is None or now < record["expires_at"]
