def conflict(tx_id, conflicting_tx_id,
             resource, reason="WRITE_CONFLICT"):
    return {"tx_id":tx_id,"conflicting_tx_id":conflicting_tx_id,
            "resource":resource,"reason":reason,
            "status":"DETECTED"}

def detected(record):
    return record["status"]=="DETECTED"
