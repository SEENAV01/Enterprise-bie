def tombstone(key,clock,reason="DELETE"):
    return {"key":key,"clock":clock,
            "reason":reason,"status":"TOMBSTONED"}

def deleted(record):
    return record["status"]=="TOMBSTONED"
