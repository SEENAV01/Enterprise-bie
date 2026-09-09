def service_contract(name,version,
                    request_schema,response_schema,
                    error_codes=None):
    return {"name":name,"version":version,
            "request_schema":request_schema,
            "response_schema":response_schema,
            "error_codes":error_codes or []}

def validate_required(payload,required):
    return all(k in payload for k in required)
