def transaction(tx_id,operations, isolation="ATOMIC"):
    if isolation not in {"ATOMIC","BEST_EFFORT"}:
        raise ValueError("INVALID_TRANSACTION_MODE")
    return {"tx_id":tx_id,"operations":operations,
            "mode":isolation,"status":"ACTIVE"}

def committed(record):
    return record["status"]=="COMMITTED"

def commit(record):
    out=dict(record); out["status"]="COMMITTED"; return out

def abort(record):
    out=dict(record); out["status"]="ABORTED"; return out
