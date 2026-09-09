def cache_entry(key,value,
                ttl_seconds=None,
                version=1):
    return {"key":key,"value":value,
            "ttl_seconds":ttl_seconds,
            "version":version,
            "status":"PRESENT"}

def present(record):
    return record["status"]=="PRESENT"
