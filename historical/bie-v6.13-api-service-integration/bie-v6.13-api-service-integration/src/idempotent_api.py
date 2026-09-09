def idempotent_request(request_id,
                      key,operation):
    return {"request_id":request_id,
            "idempotency_key":key,
            "operation":operation,
            "status":"NEW"}

def complete(record,response):
    out=dict(record)
    out["status"]="COMPLETED"
    out["response"]=response
    return out
