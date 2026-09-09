def edge_event(event_id,route_id,
              operation,status,
              upstream=None,
              latency_ms=None):
    return {"event_id":event_id,
            "route_id":route_id,
            "operation":operation,
            "status":status,
            "upstream":upstream,
            "latency_ms":latency_ms}

def metric(record):
    return {"route_id":record["route_id"],
            "status":record["status"],
            "latency_ms":record["latency_ms"]}
