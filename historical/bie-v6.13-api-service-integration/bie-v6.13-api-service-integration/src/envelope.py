def request_envelope(request_id,service,
                     operation,tenant_id=None,
                     idempotency_key=None,
                     schema_version="1"):
    return {"request_id":request_id,
            "service":service,
            "operation":operation,
            "tenant_id":tenant_id,
            "idempotency_key":idempotency_key,
            "schema_version":schema_version}

def response_envelope(request_id,status,
                      data=None,error=None,
                      schema_version="1"):
    return {"request_id":request_id,
            "status":status,
            "data":data,
            "error":error,
            "schema_version":schema_version}
