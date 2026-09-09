def retrieval_event(event_id, principal_id,
                    resource, operation, status):
    return {"event_id":event_id,"principal_id":principal_id,
            "resource":resource,"operation":operation,
            "status":status}

def successful(record):
    return record["status"]=="SUCCESS"
