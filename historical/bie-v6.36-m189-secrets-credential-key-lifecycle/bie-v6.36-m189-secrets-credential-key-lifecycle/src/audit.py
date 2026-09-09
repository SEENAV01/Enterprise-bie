def lifecycle_event(event_id, principal_id,
                    resource_id, operation, status, reason=None):
    return {"event_id":event_id,
            "principal_id":principal_id,
            "resource_id":resource_id,
            "operation":operation,
            "status":status,
            "reason":reason}

def successful(record):
    return record["status"]=="SUCCESS"
