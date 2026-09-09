def deletion_request(resource_id,
                    requested_at,
                    reason="RETENTION_EXPIRED"):
    return {"resource_id":resource_id,
            "requested_at":requested_at,
            "reason":reason,
            "status":"PENDING"}

def evaluate(request,retention_expired,
             hold_active=False):
    if hold_active:
        out=dict(request)
        out["status"]="HELD"
        return out
    if retention_expired:
        out=dict(request)
        out["status"]="APPROVED"
        return out
    out=dict(request)
    out["status"]="NOT_ELIGIBLE"
    return out
