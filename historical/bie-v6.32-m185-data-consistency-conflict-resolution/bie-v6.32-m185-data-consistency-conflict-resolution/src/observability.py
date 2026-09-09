def consistency_event(event_id,key,
                       operation,status,
                       divergence_count=0,
                       merge_count=0):
    return {"event_id":event_id,"key":key,
            "operation":operation,"status":status,
            "divergence_count":divergence_count,
            "merge_count":merge_count}

def metric(record):
    return {"key":record["key"],
            "operation":record["operation"],
            "status":record["status"],
            "divergence_count":record["divergence_count"],
            "merge_count":record["merge_count"]}
