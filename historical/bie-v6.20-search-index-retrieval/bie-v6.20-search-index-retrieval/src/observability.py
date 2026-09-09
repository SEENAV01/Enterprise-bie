def query_event(event_id,
                index,query_id,
                latency_ms,
                hits=None):
    return {"event_id":event_id,
            "index":index,
            "query_id":query_id,
            "latency_ms":latency_ms,
            "hits":hits}

def metric(record):
    return {"latency_ms":record["latency_ms"],
            "hits":record["hits"]}
