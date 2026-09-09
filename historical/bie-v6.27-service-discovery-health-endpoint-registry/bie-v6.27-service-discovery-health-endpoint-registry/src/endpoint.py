def endpoint(endpoint_id,address,
             port,protocol="HTTP",
             metadata=None):
    if port < 1 or port > 65535:
        raise ValueError("INVALID_PORT")
    return {"endpoint_id":endpoint_id,
            "address":address,"port":port,
            "protocol":protocol,
            "metadata":metadata or {},
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
