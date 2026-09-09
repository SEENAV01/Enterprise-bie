def api_contract(service,operation,
                method,path,request_schema,
                response_schema,version="1"):
    return {"service":service,
            "operation":operation,
            "method":method,
            "path":path,
            "request_schema":request_schema,
            "response_schema":response_schema,
            "version":version}

def valid(contract):
    return all(contract.get(k) for k in
               ["service","operation","method","path"])
