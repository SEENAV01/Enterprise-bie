def assessment_evidence(evidence_id,item_ref,objective_ref,
                        correct,score,misconception_refs=None,
                        confidence=None):
    return {"evidence_id":evidence_id,"item_ref":item_ref,
            "objective_ref":objective_ref,"correct":correct,
            "score":score,"misconception_refs":misconception_refs or [],
            "confidence":confidence}
