def storage_metric(event_id, namespace,
                     operation, status, latency_ms=0,
                     bytes_written=0, bytes_read=0):
    return {"event_id":event_id,"namespace":namespace,
            "operation":operation,"status":status,
            "latency_ms":latency_ms,
            "bytes_written":bytes_written,
            "bytes_read":bytes_read}

def healthy(record):
    return (record["status"]=="SUCCESS" and
            record["latency_ms"]>=0 and
            record["bytes_written"]>=0 and
            record["bytes_read"]>=0)
