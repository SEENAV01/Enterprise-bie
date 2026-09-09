from planner import plan_next_action

def compile_adaptive_plan(learner_state,actions,signals=None,
                          weights=None,constraints=None,goal=None):
    plan=plan_next_action(actions,signals,weights,constraints)
    errors=[]
    if not actions:
        errors.append("NO_CANDIDATE_ACTIONS")
    if actions and plan["selected_action"] is None:
        errors.append("NO_FEASIBLE_ACTION")
    return {"schema_version":"5.45",
            "learner_state_ref":learner_state,
            "goal":goal,
            "candidates":actions,
            "decision":plan,
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
