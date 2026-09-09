def coordination_request(request_id,
                         resource_id,
                         operation,
                         owner):
    if operation not in {"ACQUIRE","RENEW",
                         "RELEASE","TRANSFER"}:
        raise ValueError("INVALID_COORDINATION_OPERATION")
    return {"request_id":request_id,
            "resource_id":resource_id,
            "operation":operation,
            "owner":owner,
            "status":"REQUESTED"}

def complete(record,status="COMPLETED"):
    out=dict(record); out["status"]=status; return out
