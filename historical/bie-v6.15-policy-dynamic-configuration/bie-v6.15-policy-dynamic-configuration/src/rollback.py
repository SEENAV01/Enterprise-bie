def rollback(target_version,
             reason,requested_by):
    return {"target_version":target_version,
            "reason":reason,
            "requested_by":requested_by,
            "status":"REQUESTED"}

def approve(record):
    out=dict(record); out["status"]="APPROVED"; return out
