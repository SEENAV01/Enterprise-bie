def schema(schema_id, resource_id, version,
           fields=None, semantic_types=None):
    if not schema_id or not version:
        raise ValueError("INVALID_SCHEMA")
    return {"schema_id":schema_id,"resource_id":resource_id,
            "version":version,"fields":fields or [],
            "semantic_types":semantic_types or {},
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
