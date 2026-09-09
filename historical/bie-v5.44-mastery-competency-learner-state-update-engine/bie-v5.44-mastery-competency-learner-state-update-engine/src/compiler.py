from aggregation import aggregate_objective_evidence

def compile_learner_state(learner_ref,events,objective_refs,
                          competency_states=None,misconception_risks=None,
                          prerequisite_readiness=None,history=None):
    objective_states={}
    for ref in objective_refs:
        objective_states[ref]=aggregate_objective_evidence(events,ref)
    return {"schema_version":"5.44",
            "learner_ref":learner_ref,
            "objective_states":objective_states,
            "competency_states":competency_states or {},
            "misconception_risks":misconception_risks or {},
            "prerequisite_readiness":prerequisite_readiness or {},
            "history":history or [],
            "quality_gate":{"valid":True,"errors":[]}}
