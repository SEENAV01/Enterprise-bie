def quarantine(object_id,
               reason,
               scanner=None):
    return {"object_id":object_id,
            "reason":reason,
            "scanner":scanner,
            "status":"QUARANTINED"}

def release(record):
    out=dict(record); out["status"]="RELEASED"; return out

def reject(record):
    out=dict(record); out["status"]="REJECTED"; return out
