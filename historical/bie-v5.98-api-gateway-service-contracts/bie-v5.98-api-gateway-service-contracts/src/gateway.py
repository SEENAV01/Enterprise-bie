from request import normalize_path

def route(method,path,service,
          auth_scope=None,version="v1"):
    return {"method":method,
            "path":normalize_path(path),
            "service":service,
            "auth_scope":auth_scope,
            "version":version}

def route_match(request,route_record):
    return (request["method"]==route_record["method"]
            and normalize_path(request["path"])==
            route_record["path"])
