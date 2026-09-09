def memory_record(record_id,record_type,payload,version="1.0",
                 source_refs=None,concept_refs=None,tags=None):
    return {"record_id":record_id,"record_type":record_type,
            "version":version,"payload":payload,
            "source_refs":source_refs or [],
            "concept_refs":concept_refs or [],
            "tags":tags or []}
