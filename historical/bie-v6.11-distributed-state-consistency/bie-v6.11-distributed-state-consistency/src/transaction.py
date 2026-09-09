def transaction(tx_id,operations,
                isolation="READ_COMMITTED"):
    return {"tx_id":tx_id,
            "operations":operations,
            "isolation":isolation,
            "status":"PENDING"}

def commit(record):
    out=dict(record); out["status"]="COMMITTED"; return out

def abort(record,reason=None):
    out=dict(record); out["status"]="ABORTED"
    out["reason"]=reason
    return out
