def transaction(tx_id, isolation="READ_COMMITTED",
                timeout_ms=None, idempotency_key=None):
    allowed={"READ_UNCOMMITTED","READ_COMMITTED","REPEATABLE_READ","SERIALIZABLE"}
    if isolation not in allowed:
        raise ValueError("INVALID_ISOLATION")
    return {"tx_id":tx_id,"isolation":isolation,
            "timeout_ms":timeout_ms,"idempotency_key":idempotency_key,
            "status":"OPEN"}

def open_tx(record):
    return record["status"]=="OPEN"
