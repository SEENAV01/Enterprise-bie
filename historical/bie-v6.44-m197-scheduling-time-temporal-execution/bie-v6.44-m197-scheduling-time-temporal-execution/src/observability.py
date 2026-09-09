def temporal_metric(event_id, resource_id,
                     operation, status, lateness_ms=0,
                     execution_ms=0):
    return {"event_id":event_id,"resource_id":resource_id,
            "operation":operation,"status":status,
            "lateness_ms":lateness_ms,"execution_ms":execution_ms}

def healthy(record):
    return record["status"]=="SUCCESS" and record["lateness_ms"]>=0
