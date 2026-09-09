def key_reference(key_id,version,
                  purpose,algorithm=None,
                  status="ACTIVE"):
    return {"key_id":key_id,"version":version,
            "purpose":purpose,"algorithm":algorithm,
            "status":status,"kind":"KEY"}

def key_active(record):
    return record.get("status")=="ACTIVE"
