def deletion_request(request_id,
                    resource,requested_by,
                    reason=None):
    return {"request_id":request_id,
            "resource":resource,
            "requested_by":requested_by,
            "reason":reason,
            "status":"REQUESTED"}

def approve(record):
    out=dict(record); out["status"]="APPROVED"; return out

def complete(record):
    out=dict(record); out["status"]="COMPLETED"; return out
