def governance_event(event_id,resource_id,
                    operation,status,actor=None):
    return {"event_id":event_id,"resource_id":resource_id,
            "operation":operation,"status":status,"actor":actor}

def successful(record):
    return record["status"]=="SUCCESS"
