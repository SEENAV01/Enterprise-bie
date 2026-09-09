def coordination_event(event_id,
                         resource_id,
                         operation,
                         status,
                         owner=None,
                         epoch=None,
                         latency_ms=None):
    return {"event_id":event_id,
            "resource_id":resource_id,
            "operation":operation,
            "status":status,
            "owner":owner,
            "epoch":epoch,
            "latency_ms":latency_ms}

def metric(record):
    return {"status":record["status"],
            "epoch":record["epoch"],
            "latency_ms":record["latency_ms"]}
