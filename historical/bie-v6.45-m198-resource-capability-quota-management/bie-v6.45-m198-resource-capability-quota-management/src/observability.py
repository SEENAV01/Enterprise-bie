def resource_metric(event_id, resource,
                     operation, status, utilization_ratio=0,
                     allocation_amount=0):
    return {"event_id":event_id,"resource":resource,
            "operation":operation,"status":status,
            "utilization_ratio":utilization_ratio,
            "allocation_amount":allocation_amount}

def healthy(record):
    return record["status"]=="SUCCESS" and record["utilization_ratio"]>=0
