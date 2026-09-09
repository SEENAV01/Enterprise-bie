def heartbeat(worker_id, timestamp,
            load=None, sequence=None):
    return {"worker_id":worker_id,"timestamp":timestamp,
            "load":load or {},"sequence":sequence,
            "status":"HEALTHY"}

def healthy(record):
    return record["status"]=="HEALTHY"
