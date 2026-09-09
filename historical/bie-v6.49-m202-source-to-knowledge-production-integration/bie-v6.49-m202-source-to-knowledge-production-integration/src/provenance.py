def provenance(artifact_id, source_ids=None, evidence_ids=None, transform=None):
    return {"artifact_id":artifact_id,"source_ids":source_ids or [],
            "evidence_ids":evidence_ids or [],"transform":transform}

def traceable(record):
    return bool(record["source_ids"] or record["evidence_ids"])
