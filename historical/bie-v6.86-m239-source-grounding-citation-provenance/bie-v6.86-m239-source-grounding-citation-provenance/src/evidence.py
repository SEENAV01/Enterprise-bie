def evidence(evidence_id,source_id,excerpt,locator=None,kind="DIRECT"):
    return {"evidence_id":evidence_id,"source_id":source_id,"excerpt":excerpt,
            "locator":locator,"kind":kind}

def validate_evidence(e,source_ids):
    errors=[]
    if e.get("source_id") not in source_ids: errors.append("UNKNOWN_SOURCE")
    if not e.get("excerpt"): errors.append("EMPTY_EVIDENCE")
    return {"passed":not errors,"errors":errors}
