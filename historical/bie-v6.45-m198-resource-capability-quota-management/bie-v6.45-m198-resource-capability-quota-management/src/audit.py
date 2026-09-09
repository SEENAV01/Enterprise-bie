def resource_event(event_id, resource,
                     operation, status, subject=None):
    return {"event_id":event_id,"resource":resource,
            "operation":operation,"status":status,
            "subject":subject}

def successful(record):
    return record["status"]=="SUCCESS"
