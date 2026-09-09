def worker_health(worker_id, state="HEALTHY",
                 latency_ms=0, last_heartbeat=None):
    if state not in {"HEALTHY","DEGRADED","UNAVAILABLE"}:
        raise ValueError("INVALID_HEALTH_STATE")
    return {"worker_id":worker_id,"state":state,
            "latency_ms":latency_ms,
            "last_heartbeat":last_heartbeat}

def available(record):
    return record["state"]!="UNAVAILABLE"
