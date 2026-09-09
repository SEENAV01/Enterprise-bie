STATUSES={"QUEUED","RUNNING","SUCCEEDED","FAILED","RETRYING","CANCELLED"}

def job(job_id,node_id,attempt=0,status="QUEUED",priority=0,
        resources=None,payload=None):
    return {"job_id":job_id,"node_id":node_id,"attempt":attempt,
            "status":status,"priority":priority,
            "resources":resources or {},"payload":payload or {}}

def valid(j):
    return bool(j["job_id"] and j["node_id"]) and j["status"] in STATUSES
