def competency_state(competency_ref,level=None,concept_refs=None,
                     objective_refs=None,confidence=None):
    return {"competency_ref":competency_ref,"level":level,
            "concept_refs":concept_refs or [],
            "objective_refs":objective_refs or [],
            "confidence":confidence}

def competency_levels():
    return ["UNKNOWN","EMERGING","DEVELOPING","COMPETENT","ADVANCED"]
