def messaging_metric(event_id, topic_id,
                       operation, status, latency_ms=0,
                       delivery_attempt=1):
    return {"event_id":event_id,"topic_id":topic_id,
            "operation":operation,"status":status,
            "latency_ms":latency_ms,
            "delivery_attempt":delivery_attempt}

def healthy(record):
    return record["status"]=="SUCCESS" and record["latency_ms"]>=0
