def worker(worker_id,capabilities=None,status="READY",
           heartbeat_at=None):
    return {"worker_id":worker_id,
            "capabilities":capabilities or {},
            "status":status,"heartbeat_at":heartbeat_at}

def worker_can_run(worker_record,requirements):
    caps=worker_record.get("capabilities",{})
    return all(caps.get(k,0)>=v for k,v in requirements.items())
