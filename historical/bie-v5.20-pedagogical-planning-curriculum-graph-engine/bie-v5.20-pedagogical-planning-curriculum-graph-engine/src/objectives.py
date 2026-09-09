def learning_objective(objective_id,text,level,concept_refs=None,
                      assessment_targets=None):
    return {"objective_id":objective_id,"text":text,"level":level,
            "concept_refs":concept_refs or [],
            "assessment_targets":assessment_targets or []}
