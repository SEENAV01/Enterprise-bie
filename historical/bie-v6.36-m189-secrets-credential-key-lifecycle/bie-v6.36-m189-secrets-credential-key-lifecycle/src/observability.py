def key_event(event_id,key_id,version,
              operation,status):
    return {"event_id":event_id,"key_id":key_id,
            "version":version,"operation":operation,
            "status":status}

def metric(record):
    return {"key_id":record["key_id"],
            "version":record["version"],
            "operation":record["operation"],
            "status":record["status"]}
