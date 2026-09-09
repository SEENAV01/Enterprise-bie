def graph_provenance(graph_id, source_ids=None,
                    evidence_ids=None, upstream_artifacts=None):
    return {"graph_id":graph_id,"source_ids":source_ids or [],
            "evidence_ids":evidence_ids or [],
            "upstream_artifacts":upstream_artifacts or []}

def traceable(p):
    return bool(p["source_ids"]) and bool(
        p["evidence_ids"] or p["upstream_artifacts"])
