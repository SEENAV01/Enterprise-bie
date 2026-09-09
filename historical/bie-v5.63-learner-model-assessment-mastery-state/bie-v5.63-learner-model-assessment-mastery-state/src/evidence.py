def evidence(evidence_id,learner_id,activity_id,
             concept_refs=None,response=None,score=None,
             correctness=None,confidence=None,metadata=None):
    return {"evidence_id":evidence_id,"learner_id":learner_id,
            "activity_id":activity_id,"concept_refs":concept_refs or [],
            "response":response,"score":score,
            "correctness":correctness,"confidence":confidence,
            "metadata":metadata or {}}
