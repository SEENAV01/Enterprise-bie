def health_probe(instance_id,check_type,
                observed_at,status,latency_ms=None,
                details=None):
    return {"instance_id":instance_id,
            "check_type":check_type,
            "observed_at":observed_at,
            "status":status,
            "latency_ms":latency_ms,
            "details":details or {}}

def healthy(probe):
    return probe.get("status")=="HEALTHY"

def ready(probe):
    return probe.get("status")=="READY"
