def transaction_metric(event_id, tx_id,
                         operation, status,
                         latency_ms=0, conflict_count=0):
    return {"event_id":event_id,"tx_id":tx_id,
            "operation":operation,"status":status,
            "latency_ms":latency_ms,
            "conflict_count":conflict_count}

def healthy(record):
    return record["status"]=="SUCCESS" and record["latency_ms"]>=0
