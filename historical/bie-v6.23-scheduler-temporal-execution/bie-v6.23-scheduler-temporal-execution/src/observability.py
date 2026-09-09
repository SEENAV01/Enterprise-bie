def temporal_event(event_id,
                  target_id,
                  operation,
                  status,
                  scheduled_at=None,
                  started_at=None,
                  latency_ms=None):
    return {"event_id":event_id,
            "target_id":target_id,
            "operation":operation,
            "status":status,
            "scheduled_at":scheduled_at,
            "started_at":started_at,
            "latency_ms":latency_ms}

def metric(record):
    return {"status":record["status"],
            "latency_ms":record["latency_ms"]}
