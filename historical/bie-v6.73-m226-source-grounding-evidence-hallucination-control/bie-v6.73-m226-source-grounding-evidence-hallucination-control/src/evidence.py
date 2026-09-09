def evidence(evidence_id,source_id,excerpt_ref,claim_ids=None,
             relevance=0.0):
    return {"evidence_id":evidence_id,"source_id":source_id,
            "excerpt_ref":excerpt_ref,"claim_ids":claim_ids or [],
            "relevance":relevance}
def relevant(items,threshold=0.5):
    return [e for e in items if e.get("relevance",0)>=threshold]
