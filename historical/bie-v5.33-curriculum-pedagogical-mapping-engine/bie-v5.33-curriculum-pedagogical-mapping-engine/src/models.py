def learning_objective(objective_id,text,concept_refs=None,level="UNDERSTAND"):
    return {"objective_id":objective_id,"text":text,
            "concept_refs":concept_refs or [],"level":level}

def misconception(misconception_id,concept_id,belief,correction):
    return {"misconception_id":misconception_id,"concept_id":concept_id,
            "belief":belief,"correction":correction}

def mastery_checkpoint(checkpoint_id,objective_id,criterion):
    return {"checkpoint_id":checkpoint_id,"objective_id":objective_id,
            "criterion":criterion}
