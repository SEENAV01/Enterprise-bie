def resource(resource_id, resource_type,
             capacity=None, metadata=None):
    if not resource_id or not resource_type:
        raise ValueError("INVALID_RESOURCE")
    return {"resource_id":resource_id,"resource_type":resource_type,
            "capacity":capacity,"metadata":metadata or {},
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
