def provenance(job_id, source_refs=None, event_ids=None,
               artifact_ids=None, checkpoint_ids=None):
    return {"job_id":job_id,"source_refs":source_refs or [],
            "event_ids":event_ids or [],"artifact_ids":artifact_ids or [],
            "checkpoint_ids":checkpoint_ids or []}

def traceable(p):
    return bool(p["job_id"] and p["source_refs"] and
                (p["event_ids"] or p["artifact_ids"]))
