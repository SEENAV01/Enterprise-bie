def cache_event(event_id,key,
               operation,status,
               latency_ms=None,
               lag_seconds=None):
    return {"event_id":event_id,
            "key":key,"operation":operation,
            "status":status,
            "latency_ms":latency_ms,
            "lag_seconds":lag_seconds}

def metric(record):
    return {"operation":record["operation"],
            "status":record["status"],
            "latency_ms":record["latency_ms"],
            "lag_seconds":record["lag_seconds"]}
