def transaction(tx_id,
                isolation="READ_COMMITTED"):
    if isolation not in {"READ_COMMITTED",
                         "REPEATABLE_READ",
                         "SERIALIZABLE"}:
        raise ValueError("INVALID_ISOLATION")
    return {"tx_id":tx_id,
            "isolation":isolation,
            "status":"OPEN"}

def commit(record):
    out=dict(record); out["status"]="COMMITTED"; return out

def rollback(record):
    out=dict(record); out["status"]="ROLLED_BACK"; return out
