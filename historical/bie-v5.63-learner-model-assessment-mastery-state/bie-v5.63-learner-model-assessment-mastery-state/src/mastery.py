def mastery_state(learner_id,concept_id,estimate=0.0,
                  uncertainty=1.0,evidence_refs=None,
                  status="UNKNOWN",updated_at=None):
    return {"learner_id":learner_id,"concept_id":concept_id,
            "estimate":estimate,"uncertainty":uncertainty,
            "evidence_refs":evidence_refs or [],
            "status":status,"updated_at":updated_at}

def classify_mastery(estimate,uncertainty,mastered=0.8,
                     developing=0.5):
    if estimate>=mastered and uncertainty<=0.25: return "MASTERED"
    if estimate>=developing: return "DEVELOPING"
    return "NEEDS_SUPPORT"
