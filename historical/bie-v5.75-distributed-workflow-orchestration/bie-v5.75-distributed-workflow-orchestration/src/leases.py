def lease(job_id,worker_id,expires_at):
    return {"job_id":job_id,"worker_id":worker_id,
            "expires_at":expires_at,"status":"ACTIVE"}

def lease_expired(lease_record,current_time):
    return current_time>=lease_record["expires_at"]

def release(lease_record):
    out=dict(lease_record); out["status"]="RELEASED"; return out
