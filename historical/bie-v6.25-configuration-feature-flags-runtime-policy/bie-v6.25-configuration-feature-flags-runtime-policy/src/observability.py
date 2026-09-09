def config_event(event_id,key,
                operation,status,
                scope=None,source=None):
    return {"event_id":event_id,
            "key":key,
            "operation":operation,
            "status":status,
            "scope":scope,
            "source":source}

def metric(record):
    return {"key":record["key"],
            "operation":record["operation"],
            "status":record["status"]}
