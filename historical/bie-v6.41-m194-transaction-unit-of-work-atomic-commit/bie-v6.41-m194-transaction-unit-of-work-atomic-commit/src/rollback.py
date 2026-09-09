def rollback(tx_id, reason=None):
    return {"tx_id":tx_id,"reason":reason,
            "status":"ROLLED_BACK"}

def rolled_back(record):
    return record["status"]=="ROLLED_BACK"
