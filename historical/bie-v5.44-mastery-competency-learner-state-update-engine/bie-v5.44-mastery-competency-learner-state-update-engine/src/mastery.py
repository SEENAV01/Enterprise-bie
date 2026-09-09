def mastery_state(objective_ref,level=None,evidence_count=0,
                  confidence=None,trend=None,last_updated=None):
    return {"objective_ref":objective_ref,"level":level,
            "evidence_count":evidence_count,"confidence":confidence,
            "trend":trend,"last_updated":last_updated}

def mastery_levels():
    return ["UNKNOWN","EMERGING","DEVELOPING","PROFICIENT","MASTERED"]
