def transaction_event(event_id,tx_id,
                       operation,status,
                       latency_ms=None,
                       duplicate=False):
    return {"event_id":event_id,
            "tx_id":tx_id,
            "operation":operation,
            "status":status,
            "latency_ms":latency_ms,
            "duplicate":duplicate}

def metric(record):
    return {"tx_id":record["tx_id"],
            "operation":record["operation"],
            "status":record["status"],
            "latency_ms":record["latency_ms"],
            "duplicate":record["duplicate"]}
