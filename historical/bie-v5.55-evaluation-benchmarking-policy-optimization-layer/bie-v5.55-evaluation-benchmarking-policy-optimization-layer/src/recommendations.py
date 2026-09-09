def recommendation(rec_id,policy_ref,action,confidence,
                   evidence_refs=None,expected_effects=None,
                   risks=None):
    return {"recommendation_id":rec_id,"policy_ref":policy_ref,
            "action":action,"confidence":confidence,
            "evidence_refs":evidence_refs or [],
            "expected_effects":expected_effects or {},
            "risks":risks or {}}

def bounded_recommendation(rec,threshold=0.8):
    if rec.get("confidence",0) < threshold:
        rec=dict(rec)
        rec["action"]="HUMAN_REVIEW"
        rec["bounded"]=True
    else:
        rec=dict(rec)
        rec["bounded"]=True
    return rec
