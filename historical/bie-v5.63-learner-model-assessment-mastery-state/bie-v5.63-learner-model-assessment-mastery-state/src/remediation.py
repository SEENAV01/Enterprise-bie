def remediation_rule(concept_id,threshold=0.5,
                     uncertainty=0.35,strategies=None):
    return {"concept_id":concept_id,"threshold":threshold,
            "uncertainty":uncertainty,
            "strategies":strategies or ["EXPLAIN","PRACTICE"]}

def recommend_remediation(state,rule):
    if (state.get("estimate",0.0)<rule["threshold"] or
        state.get("uncertainty",1.0)>rule["uncertainty"]):
        return rule["strategies"]
    return []
