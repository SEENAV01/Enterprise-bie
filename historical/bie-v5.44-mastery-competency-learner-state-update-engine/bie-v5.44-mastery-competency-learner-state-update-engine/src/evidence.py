def evidence_event(evidence_id,evidence_type,objective_ref,
                  concept_refs=None,score=None,correct=None,
                  confidence=None,diagnosis_refs=None,timestamp=None):
    return {"evidence_id":evidence_id,"evidence_type":evidence_type,
            "objective_ref":objective_ref,"concept_refs":concept_refs or [],
            "score":score,"correct":correct,"confidence":confidence,
            "diagnosis_refs":diagnosis_refs or [],
            "timestamp":timestamp}

def evidence_weight(event):
    base=1.0
    if event.get("confidence") is not None:
        base*=max(0.0,min(1.0,event["confidence"]))
    return base
