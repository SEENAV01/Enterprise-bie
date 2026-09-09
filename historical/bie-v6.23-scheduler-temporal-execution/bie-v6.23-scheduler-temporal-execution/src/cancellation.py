def cancellation(target_id,
                  reason):
    return {"target_id":target_id,
            "reason":reason,
            "status":"REQUESTED"}

def complete(record):
    out=dict(record); out["status"]="CANCELLED"; return out
