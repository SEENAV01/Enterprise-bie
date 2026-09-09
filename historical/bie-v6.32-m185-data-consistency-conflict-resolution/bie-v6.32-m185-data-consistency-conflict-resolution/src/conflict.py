def conflict(key,left,right,reason="CONCURRENT_WRITES"):
    return {"key":key,"left":left,"right":right,
            "reason":reason,"status":"DETECTED"}

def detected(record):
    return record["status"]=="DETECTED"
