def attempt(attempt_id,job_id,worker_id,number,status,
            checkpoint_ref=None,error=None):
    return {"attempt_id":attempt_id,"job_id":job_id,
            "worker_id":worker_id,"number":number,"status":status,
            "checkpoint_ref":checkpoint_ref,"error":error}

def successful(a):
    return a["status"]=="SUCCEEDED"
