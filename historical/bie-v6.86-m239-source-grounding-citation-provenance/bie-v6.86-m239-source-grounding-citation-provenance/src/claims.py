def grounded_claim(claim_id,text,evidence_ids=None,confidence=0.0):
    return {"claim_id":claim_id,"text":text,"evidence_ids":evidence_ids or [],
            "confidence":float(confidence)}

def verify_claim(c,evidence_by_id,minimum_confidence=0.7):
    errors=[]
    if not c.get("text"): errors.append("EMPTY_CLAIM")
    if not c.get("evidence_ids"): errors.append("NO_EVIDENCE")
    for eid in c.get("evidence_ids",[]):
        if eid not in evidence_by_id: errors.append("UNKNOWN_EVIDENCE:"+eid)
    if c.get("confidence",0)<minimum_confidence: errors.append("LOW_CONFIDENCE")
    return {"passed":not errors,"errors":errors}
