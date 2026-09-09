def entity(entity_id,entity_type,
            tenant_id=None,state=None,
            version=0):
    return {"entity_id":entity_id,
            "entity_type":entity_type,
            "tenant_id":tenant_id,
            "state":state or {},
            "version":version}

def version(record):
    return record.get("version",0)
