def wait_condition(wait_id,
                   workflow_id,
                   condition,
                   timeout_at=None):
    return {"wait_id":wait_id,
            "workflow_id":workflow_id,
            "condition":condition,
            "timeout_at":timeout_at,
            "status":"WAITING"}

def satisfy(record):
    out=dict(record); out["status"]="SATISFIED"; return out
