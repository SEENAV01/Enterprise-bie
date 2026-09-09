def entity(entity_id,name,entity_type=None,source_refs=None):
    return {"entity_id":entity_id,"name":name,"entity_type":entity_type,
            "source_refs":source_refs or []}
