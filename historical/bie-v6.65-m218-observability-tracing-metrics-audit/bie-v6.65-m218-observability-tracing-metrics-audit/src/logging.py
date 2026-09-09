def log(level,message,trace_id=None,span_id=None,job_id=None,
        node_id=None,fields=None):
    if level not in {"DEBUG","INFO","WARN","ERROR","CRITICAL"}:
        raise ValueError("INVALID_LOG_LEVEL")
    return {"level":level,"message":message,"trace_id":trace_id,
            "span_id":span_id,"job_id":job_id,"node_id":node_id,
            "fields":fields or {}}
