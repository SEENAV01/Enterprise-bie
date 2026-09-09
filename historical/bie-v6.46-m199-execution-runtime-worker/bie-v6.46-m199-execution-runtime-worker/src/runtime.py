def runtime(runtime_id, runtime_type,
            version=None, environment=None):
    if not runtime_id or not runtime_type:
        raise ValueError("INVALID_RUNTIME")
    return {"runtime_id":runtime_id,"runtime_type":runtime_type,
            "version":version,"environment":environment or {},
            "status":"AVAILABLE"}

def available(record):
    return record["status"]=="AVAILABLE"
