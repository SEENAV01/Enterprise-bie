def diagnosis(diagnosis_id,category,concept_refs=None,
              evidence_refs=None,confidence=None,notes=None):
    return {"diagnosis_id":diagnosis_id,"category":category,
            "concept_refs":concept_refs or [],
            "evidence_refs":evidence_refs or [],
            "confidence":confidence,"notes":notes}

def diagnosis_categories():
    return ["CONCEPT_GAP","PREREQUISITE_GAP","MISCONCEPTION",
            "PROCEDURAL_ERROR","REPRESENTATION_GAP",
            "POSSIBLE_CARELESS_ERROR","UNKNOWN"]
