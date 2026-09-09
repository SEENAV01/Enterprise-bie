def response(request_id,status,body=None,
             headers=None,correlation_id=None):
    return {"request_id":request_id,"status":status,
            "body":body,"headers":headers or {},
            "correlation_id":correlation_id}

def success(status=200,body=None,**kwargs):
    return response(kwargs.pop("request_id",""),
                    status,body,correlation_id=kwargs.get("correlation_id"))
