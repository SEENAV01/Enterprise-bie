def heartbeat(worker_id,observed_at,status,
              load=None):
    return {"worker_id":worker_id,
            "observed_at":observed_at,
            "status":status,"load":load or {}}

def healthy(last_seen,now,max_age):
    return now-last_seen<=max_age
