def capability(capability_id, resource_id,
               name, units=None, attributes=None):
    return {"capability_id":capability_id,
            "resource_id":resource_id,"name":name,
            "units":units,"attributes":attributes or {},
            "status":"AVAILABLE"}

def available(record):
    return record["status"]=="AVAILABLE"
