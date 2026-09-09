def job(job_id, workload, priority=0,
        deadline=None, metadata=None):
    return {"job_id":job_id,"workload":workload,
            "priority":priority,"deadline":deadline,
            "metadata":metadata or {},"status":"QUEUED"}

def queued(record):
    return record["status"]=="QUEUED"
