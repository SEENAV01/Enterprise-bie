def learner_model(learner_id,states=None,
                  preferences=None,constraints=None):
    return {"learner_id":learner_id,"states":states or [],
            "preferences":preferences or {},
            "constraints":constraints or {}}

def get_state(model,concept_id):
    for s in model.get("states",[]):
        if s.get("concept_id")==concept_id: return s
    return None
