def adaptive_decision(state,misconceptions=None):
    misconceptions=misconceptions or []
    if state.get("status")=="MASTERED":
        return {"action":"ADVANCE","reason":"OBJECTIVE_MASTERED"}
    if misconceptions:
        return {"action":"REMEDIATE","reason":"MISCONCEPTION_DETECTED",
                "misconceptions":misconceptions}
    return {"action":"REVIEW","reason":"MASTERY_NOT_ESTABLISHED"}

def choose_next_objective(ordered_objectives,states):
    done={s["objective_id"] for s in states if s.get("status")=="MASTERED"}
    for obj in ordered_objectives:
        if obj["objective_id"] not in done:
            return obj["objective_id"]
    return None
