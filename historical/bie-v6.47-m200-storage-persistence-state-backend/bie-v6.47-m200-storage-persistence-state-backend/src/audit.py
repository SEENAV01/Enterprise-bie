def storage_event(event_id, namespace,
                   operation, status, key=None):
    return {"event_id":event_id,"namespace":namespace,
            "operation":operation,"status":status,"key":key}

def successful(record):
    return record["status"]=="SUCCESS"
