def secret_ref(secret_id, version=None, scope=None):
    if not secret_id:
        raise ValueError("INVALID_SECRET_ID")
    return {"secret_id":secret_id,"version":version,
            "scope":scope,"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
