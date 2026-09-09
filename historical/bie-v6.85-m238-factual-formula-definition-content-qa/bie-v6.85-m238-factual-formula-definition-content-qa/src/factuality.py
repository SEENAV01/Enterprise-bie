def claim(claim_id,text,source_refs=None,confidence=1.0):
    return {"claim_id":claim_id,"text":text,"source_refs":source_refs or [],
            "confidence":float(confidence)}

def validate_claim(c,require_source=False):
    errors=[]
    if not c.get("text"): errors.append("EMPTY_CLAIM")
    if not 0<=c.get("confidence",0)<=1: errors.append("INVALID_CONFIDENCE")
    if require_source and not c.get("source_refs"): errors.append("MISSING_SOURCE")
    return {"passed":not errors,"errors":errors}
