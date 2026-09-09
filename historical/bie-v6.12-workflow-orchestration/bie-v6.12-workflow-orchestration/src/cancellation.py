def cancellation(workflow_id,
                  requested_by,
                  reason=None):
    return {"workflow_id":workflow_id,
            "requested_by":requested_by,
            "reason":reason,
            "status":"REQUESTED"}

def approve(record):
    out=dict(record); out["status"]="APPROVED"; return out

def reject(record):
    out=dict(record); out["status"]="REJECTED"; return out
