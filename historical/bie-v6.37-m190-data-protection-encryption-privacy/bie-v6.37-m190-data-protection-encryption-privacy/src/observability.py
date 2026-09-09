def protection_metric(event_id, data_type,
                      classification, operation, status):
    return {"event_id":event_id,"data_type":data_type,
            "classification":classification,
            "operation":operation,"status":status}

def metric(record):
    return dict(record)
