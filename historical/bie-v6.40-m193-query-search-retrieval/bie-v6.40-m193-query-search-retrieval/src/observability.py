def retrieval_metric(event_id, resource,
                     latency_ms, result_count, status):
    return {"event_id":event_id,"resource":resource,
            "latency_ms":latency_ms,"result_count":result_count,
            "status":status}

def healthy(record):
    return record["status"]=="SUCCESS" and record["latency_ms"]>=0
