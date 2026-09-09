def search_event(event_id,index_name,
                operation,status,
                latency_ms=None,
                hits=None):
    return {"event_id":event_id,
            "index_name":index_name,
            "operation":operation,
            "status":status,
            "latency_ms":latency_ms,
            "hits":hits}

def metric(record):
    return {"index_name":record["index_name"],
            "operation":record["operation"],
            "status":record["status"],
            "latency_ms":record["latency_ms"],
            "hits":record["hits"]}
