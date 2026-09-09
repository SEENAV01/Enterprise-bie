def learner_state(learner_ref,objective_states=None,
                  competency_states=None,misconception_risks=None,
                  prerequisite_readiness=None,history=None):
    return {"learner_ref":learner_ref,
            "objective_states":objective_states or {},
            "competency_states":competency_states or {},
            "misconception_risks":misconception_risks or {},
            "prerequisite_readiness":prerequisite_readiness or {},
            "history":history or []}

def state_update(previous,new_evidence):
    return {"previous":previous,"new_evidence":new_evidence,
            "requires_recompute":True}
