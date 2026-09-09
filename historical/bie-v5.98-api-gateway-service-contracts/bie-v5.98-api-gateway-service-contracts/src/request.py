def request(request_id,method,path,headers=None,
            query=None,body=None,correlation_id=None):
    return {"request_id":request_id,"method":method,
            "path":path,"headers":headers or {},
            "query":query or {},"body":body,
            "correlation_id":correlation_id}

def normalize_path(path):
    return "/" + path.strip("/")
