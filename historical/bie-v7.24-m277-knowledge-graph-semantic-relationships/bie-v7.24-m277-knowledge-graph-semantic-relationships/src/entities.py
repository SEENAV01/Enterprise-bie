def create_entity(entity_id, entity_type, name, attributes=None):
    return {"entity_id":entity_id,"entity_type":entity_type,"name":name,
            "attributes":attributes or {}}

def resolve_entity(entities, candidate):
    matches=[e for e in entities if e["name"].strip().lower()==candidate.strip().lower()]
    return {"resolved":len(matches)==1,"entity":matches[0] if len(matches)==1 else None,
            "candidates":matches}
