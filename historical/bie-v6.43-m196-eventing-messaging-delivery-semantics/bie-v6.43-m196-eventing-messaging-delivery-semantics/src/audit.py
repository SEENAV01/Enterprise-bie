def messaging_event(event_id, operation,
                     resource, status, actor=None):
    return {"event_id":event_id,"operation":operation,
            "resource":resource,"status":status,"actor":actor}

def successful(record):
    return record["status"]=="SUCCESS"
