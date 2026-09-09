def adaptive_plan(concepts,masteries,dependency_map=None):
    dependency_map=dependency_map or {}
    plan=[]
    for c in prioritize_concepts(concepts,masteries):
        m=masteries.get(c,0)
        action=("ADVANCE" if m>=0.85 else
                "TARGETED_PRACTICE" if m>=0.60 else "RETEACH_AND_PRACTICE")
        plan.append({"concept_id":c,"mastery":m,"action":action,
                     "prerequisites":dependency_map.get(c,[])})
    return plan

def prioritize_concepts(concepts,masteries):
    return sorted(concepts,key=lambda c:masteries.get(c,0))
