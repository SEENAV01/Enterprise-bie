def lineage_metric(event_id,resource_id,
                    operation,status,edge_count=0):
    return {"event_id":event_id,"resource_id":resource_id,
            "operation":operation,"status":status,
            "edge_count":edge_count}

def metric(record):
    return dict(record)
