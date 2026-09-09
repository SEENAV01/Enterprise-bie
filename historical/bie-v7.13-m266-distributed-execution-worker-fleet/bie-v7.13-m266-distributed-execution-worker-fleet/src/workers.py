def register_worker(worker_id, capabilities, capacity=1):
    return {"worker_id":worker_id,"capabilities":set(capabilities),
            "capacity":capacity,"status":"HEALTHY","active_jobs":0,"heartbeat":0}

def heartbeat(worker, timestamp):
    worker["heartbeat"]=timestamp
    worker["status"]="HEALTHY"
    return worker

def mark_unhealthy(worker):
    worker["status"]="UNHEALTHY"
    return worker
