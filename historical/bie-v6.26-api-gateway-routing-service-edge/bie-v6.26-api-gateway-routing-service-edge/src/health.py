def health(endpoint,status="HEALTHY",
           latency_ms=None):
    if status not in {"HEALTHY","UNHEALTHY","UNKNOWN"}:
        raise ValueError("INVALID_HEALTH_STATUS")
    return {"endpoint":endpoint,"status":status,
            "latency_ms":latency_ms}

def routable(record):
    return record["status"]=="HEALTHY"
