def lineage(artifact_id, parents=None, source_refs=None):
    return {"artifact_id":artifact_id,
            "parents":parents or [],
            "source_refs":source_refs or []}

def traceable(record):
    return bool(record["source_refs"] or record["parents"])
