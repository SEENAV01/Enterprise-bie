def cache_event(event_id,
                cache,key,operation,
                hit=None,latency_ms=None):
    return {"event_id":event_id,
            "cache":cache,
            "key":key,
            "operation":operation,
            "hit":hit,
            "latency_ms":latency_ms}

def metric(record):
    return {"hit":record["hit"],
            "latency_ms":record["latency_ms"]}
