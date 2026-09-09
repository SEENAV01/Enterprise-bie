def acquire_lease(job_id, worker_id, lease_id, expires_at):
    return {"job_id":job_id,"worker_id":worker_id,"lease_id":lease_id,
            "expires_at":expires_at,"status":"ACTIVE"}

def renew_lease(lease, expires_at):
    lease["expires_at"]=expires_at
    lease["status"]="ACTIVE"
    return lease

def expire_lease(lease):
    lease["status"]="EXPIRED"
    return lease
