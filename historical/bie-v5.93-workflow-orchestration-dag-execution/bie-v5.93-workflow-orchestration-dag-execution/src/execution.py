def execution(workflow_id,status="PENDING",
              completed=None,failed=None,
              cancelled=False):
    return {"workflow_id":workflow_id,
            "status":status,
            "completed":completed or [],
            "failed":failed or [],
            "cancelled":cancelled}

def transition(record,status):
    out=dict(record); out["status"]=status
    return out
