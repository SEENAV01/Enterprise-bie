from scoring import score_action,rank_actions
from constraints import satisfies_constraints

def plan_next_action(actions,signals=None,weights=None,constraints=None):
    allowed=[]
    rejected=[]
    for a in actions:
        errors=satisfies_constraints(a,constraints or [])
        if errors:
            rejected.append({"action_id":a.get("action_id"),"errors":errors})
        else:
            allowed.append(a)
    scores={a["action_id"]:score_action(a,signals,weights) for a in allowed}
    ranked=rank_actions(allowed,scores)
    return {"ranked_actions":ranked,
            "scores":scores,
            "rejected":rejected,
            "selected_action":ranked[0] if ranked else None}
