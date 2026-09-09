def lease(job_id,worker_id,lease_id,expires_at,
          attempt=1):
    return {"job_id":job_id,"worker_id":worker_id,
            "lease_id":lease_id,"expires_at":expires_at,
            "attempt":attempt,"status":"ACTIVE"}

def lease_valid(lease_record,now):
    return (lease_record.get("status")=="ACTIVE" and
            now < lease_record.get("expires_at",now))

def release_lease(record,status="RELEASED"):
    out=dict(record); out["status"]=status
    return out
