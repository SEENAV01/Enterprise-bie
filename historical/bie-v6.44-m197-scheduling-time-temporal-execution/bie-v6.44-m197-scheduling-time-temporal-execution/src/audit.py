def temporal_event(event_id, resource_id,
                  operation, status, timestamp=None):
    return {"event_id":event_id,"resource_id":resource_id,
            "operation":operation,"status":status,
            "timestamp":timestamp}

def successful(record):
    return record["status"]=="SUCCESS"
