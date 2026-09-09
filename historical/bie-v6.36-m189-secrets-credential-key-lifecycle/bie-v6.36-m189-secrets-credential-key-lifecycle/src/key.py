def key_record(key_id, algorithm, version=1,
              purpose=None, status="ACTIVE"):
    if status not in {"ACTIVE","DISABLED","REVOKED","EXPIRED"}:
        raise ValueError("INVALID_KEY_STATUS")
    return {"key_id":key_id,"algorithm":algorithm,
            "version":version,"purpose":purpose,"status":status}

def usable(record):
    return record["status"]=="ACTIVE"
