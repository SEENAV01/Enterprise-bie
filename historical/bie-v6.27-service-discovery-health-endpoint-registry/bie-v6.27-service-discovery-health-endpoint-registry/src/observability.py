def registry_event(event_id,
                  service_id,endpoint_id,
                  operation,status,
                  region=None,zone=None):
    return {"event_id":event_id,
            "service_id":service_id,
            "endpoint_id":endpoint_id,
            "operation":operation,
            "status":status,
            "region":region,
            "zone":zone}

def metric(record):
    return {"service_id":record["service_id"],
            "endpoint_id":record["endpoint_id"],
            "operation":record["operation"],
            "status":record["status"]}
