def learning_evidence(objective_id,evidence_type,score=None,
                      misconception_refs=None,attempt_id=None):
    return {"objective_id":objective_id,"evidence_type":evidence_type,
            "score":score,"misconception_refs":misconception_refs or [],
            "attempt_id":attempt_id}
