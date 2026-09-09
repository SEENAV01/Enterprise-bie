def coordination_event(event_id, coordination_id,
                        operation, status, actor=None):
    return {"event_id":event_id,"coordination_id":coordination_id,
            "operation":operation,"status":status,"actor":actor}

def successful(record):
    return record["status"]=="SUCCESS"
