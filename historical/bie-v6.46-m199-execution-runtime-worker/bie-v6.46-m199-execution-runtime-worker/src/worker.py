def worker(worker_id, runtime_id=None, capabilities=None,
           metadata=None):
    if not worker_id:
        raise ValueError("INVALID_WORKER")
    return {"worker_id":worker_id,"runtime_id":runtime_id,
            "capabilities":capabilities or [],
            "metadata":metadata or {},"status":"READY"}

def ready(record):
    return record["status"]=="READY"
