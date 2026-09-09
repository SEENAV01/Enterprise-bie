def estimate_granularity(unit):
    concepts=len(unit.get("concept_ids",[]))
    minutes=float(unit.get("duration_minutes",5))
    return {"concepts":concepts,"duration_minutes":minutes,
            "concepts_per_minute":round(concepts/minutes,3) if minutes else concepts}

def validate_granularity(g,min_minutes=2,max_minutes=15,max_concepts=3):
    errors=[]
    if g["duration_minutes"]<min_minutes: errors.append("UNIT_TOO_SHORT")
    if g["duration_minutes"]>max_minutes: errors.append("UNIT_TOO_LONG")
    if g["concepts"]>max_concepts: errors.append("TOO_MANY_CONCEPTS")
    return {"passed":not errors,"errors":errors}
