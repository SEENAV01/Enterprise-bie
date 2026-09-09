def route(route_id,path,method,
          upstream,version=None):
    if method not in {"GET","POST","PUT","PATCH",
                      "DELETE","HEAD","OPTIONS"}:
        raise ValueError("INVALID_METHOD")
    return {"route_id":route_id,"path":path,
            "method":method,"upstream":upstream,
            "version":version,"enabled":True}

def matches(record,path,method):
    return record["enabled"] and record["method"]==method and record["path"]==path
