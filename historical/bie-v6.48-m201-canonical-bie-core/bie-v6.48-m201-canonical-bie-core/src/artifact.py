def artifact(artifact_id, kind, producer_stage,
             content_ref, source_refs=None, metadata=None):
    return {"artifact_id":artifact_id,"kind":kind,
            "producer_stage":producer_stage,
            "content_ref":content_ref,
            "source_refs":source_refs or [],
            "metadata":metadata or {}}

def grounded(record):
    return bool(record["source_refs"])
