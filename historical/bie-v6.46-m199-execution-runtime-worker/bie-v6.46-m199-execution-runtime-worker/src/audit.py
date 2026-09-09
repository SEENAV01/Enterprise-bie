def execution_event(event_id, resource,
                     operation, status, actor=None):
    return {"event_id":event_id,"resource":resource,
            "operation":operation,"status":status,"actor":actor}

def successful(record):
    return record["status"]=="SUCCESS"
