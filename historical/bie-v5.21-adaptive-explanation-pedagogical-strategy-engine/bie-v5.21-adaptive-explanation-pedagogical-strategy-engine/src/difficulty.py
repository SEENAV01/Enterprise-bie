def difficulty(concept_id,level,confidence=None,
               prerequisite_count=0,misconception_risk=0.0):
    return {"concept_id":concept_id,"level":level,"confidence":confidence,
            "prerequisite_count":prerequisite_count,
            "misconception_risk":misconception_risk}

def adjust_for_mastery(difficulty_level,mastery):
    if mastery is None: return difficulty_level
    if mastery<0.35: return "FOUNDATIONAL"
    if mastery<0.7: return difficulty_level
    return "EXTENSION"
