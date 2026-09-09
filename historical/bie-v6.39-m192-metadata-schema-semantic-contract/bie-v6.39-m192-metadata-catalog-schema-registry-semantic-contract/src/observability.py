def schema_metric(event_id, schema_id,
                  version, operation, status):
    return {"event_id":event_id,"schema_id":schema_id,
            "version":version,"operation":operation,
            "status":status}

def metric(record):
    return dict(record)
