def prerequisite_readiness(concept_id,prerequisites,mastery):
    scores=[mastery.get(p,0) for p in prerequisites]
    ready=all(x>=0.65 for x in scores)
    return {"concept_id":concept_id,"prerequisites":prerequisites,
            "scores":scores,"ready":ready}

def readiness_gate(records):
    return {"passed":all(r["ready"] for r in records),"records":records}
