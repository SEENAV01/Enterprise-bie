def metadata(resource_id, name, description=None,
             owner=None, tags=None):
    if not resource_id or not name:
        raise ValueError("INVALID_METADATA")
    return {"resource_id":resource_id,"name":name,
            "description":description,"owner":owner,
            "tags":tags or {},"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
