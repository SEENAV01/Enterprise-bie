def protection_event(event_id, principal_id,
                    data_type, operation, status, reason=None):
    return {"event_id":event_id,"principal_id":principal_id,
            "data_type":data_type,"operation":operation,
            "status":status,"reason":reason}

def successful(record):
    return record["status"]=="SUCCESS"
