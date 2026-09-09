def worker(worker_id,capabilities=None,resources=None,
           environment=None,status="READY"):
    return {"worker_id":worker_id,
            "capabilities":capabilities or [],
            "resources":resources or {},
            "environment":environment or {},
            "status":status}

def register(worker_record):
    out=dict(worker_record)
    out["status"]="REGISTERED"
    return out
