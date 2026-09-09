def provenance(artifact_id, source_ids=None,
               graph_ids=None, evidence_ids=None, upstream_artifacts=None):
    return {"artifact_id": artifact_id,
            "source_ids": source_ids or [],
            "graph_ids": graph_ids or [],
            "evidence_ids": evidence_ids or [],
            "upstream_artifacts": upstream_artifacts or []}

def traceable(p):
    return bool(p["source_ids"] or p["graph_ids"] or p["upstream_artifacts"])
