def misconception_intervention(concept_id,misconception_id,
                                intervention_type="CONTRAST",
                                evidence_refs=None):
    return {"concept_id":concept_id,"misconception_id":misconception_id,
            "intervention_type":intervention_type,
            "evidence_refs":evidence_refs or []}

def choose_intervention(risk):
    if risk>=0.75: return "CONTRAST_PLUS_TARGETED_PRACTICE"
    if risk>=0.45: return "CONTRAST"
    return "NORMAL_EXPLANATION"
