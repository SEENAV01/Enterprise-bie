def health(endpoint_id,status="HEALTHY",
           latency_ms=None,checked_at=None):
    if status not in {"HEALTHY","UNHEALTHY","UNKNOWN"}:
        raise ValueError("INVALID_HEALTH_STATUS")
    return {"endpoint_id":endpoint_id,
            "status":status,"latency_ms":latency_ms,
            "checked_at":checked_at}

def routable(record):
    return record["status"]=="HEALTHY"
