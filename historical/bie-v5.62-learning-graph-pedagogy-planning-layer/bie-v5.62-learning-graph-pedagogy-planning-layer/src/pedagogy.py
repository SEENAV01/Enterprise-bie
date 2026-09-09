def learning_step(step_id,concept_refs,objective_refs,
                 strategy="EXPLAIN_PRACTICE",
                 modalities=None,assessment=None,
                 misconception_refs=None):
    return {"step_id":step_id,"concept_refs":concept_refs,
            "objective_refs":objective_refs,"strategy":strategy,
            "modalities":modalities or [],
            "assessment":assessment or {},
            "misconception_refs":misconception_refs or []}

def pedagogy_plan(plan_id,steps=None,learner_model=None,
                  constraints=None):
    return {"plan_id":plan_id,"steps":steps or [],
            "learner_model":learner_model or {},
            "constraints":constraints or {}}
