def lease(task_id,worker_id,expires_at):
    return {"task_id":task_id,"worker_id":worker_id,
            "expires_at":expires_at,"status":"LEASED"}

def release(lease_record):
    out=dict(lease_record); out["status"]="RELEASED"
    return out
