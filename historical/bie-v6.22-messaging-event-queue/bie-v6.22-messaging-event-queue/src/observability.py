def messaging_event(event_id,
                    entity_id,
                    operation,
                    status,
                    latency_ms=None,
                    attempt=None):
    return {"event_id":event_id,
            "entity_id":entity_id,
            "operation":operation,
            "status":status,
            "latency_ms":latency_ms,
            "attempt":attempt}

def metric(record):
    return {"status":record["status"],
            "latency_ms":record["latency_ms"],
            "attempt":record["attempt"]}
