from identity import stable_hash

def provenance_record(entity_id,entity_type,source_refs=None,
                      model_refs=None,prompt_refs=None,build_ref=None):
    return {"entity_id":entity_id,"entity_type":entity_type,
            "source_refs":source_refs or [],"model_refs":model_refs or [],
            "prompt_refs":prompt_refs or [],"build_ref":build_ref}

def lineage_hash(record):
    return stable_hash(record)
