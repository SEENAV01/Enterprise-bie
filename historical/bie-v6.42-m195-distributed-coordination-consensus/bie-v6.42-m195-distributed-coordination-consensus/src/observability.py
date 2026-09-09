def coordination_metric(event_id, coordination_id,
                         term, operation, status,
                         latency_ms=0, quorum_reached=False):
    return {"event_id":event_id,"coordination_id":coordination_id,
            "term":term,"operation":operation,"status":status,
            "latency_ms":latency_ms,
            "quorum_reached":quorum_reached}

def healthy(record):
    return record["status"]=="SUCCESS" and record["latency_ms"]>=0
