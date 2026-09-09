def storage_event(event_id,
                 object_id,
                 operation,
                 status,
                 bytes_count=None,
                 latency_ms=None):
    return {"event_id":event_id,
            "object_id":object_id,
            "operation":operation,
            "status":status,
            "bytes_count":bytes_count,
            "latency_ms":latency_ms}

def metric(record):
    return {"object_id":record["object_id"],
            "operation":record["operation"],
            "status":record["status"],
            "bytes_count":record["bytes_count"],
            "latency_ms":record["latency_ms"]}
