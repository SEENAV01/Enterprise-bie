def create_state(problem_id, steps):
    return {"problem_id":problem_id,"current_step":0,"steps":steps,
            "responses":[],"status":"ACTIVE","hint_level":"CONCEPT"}

def record_response(state, response, expected=None):
    correct = expected is None or response == expected
    state["responses"].append({"step":state["current_step"],"response":response,"correct":correct})
    if correct:
        state["current_step"] += 1
    return state

def complete(state):
    if state["current_step"] >= len(state["steps"]):
        state["status"]="COMPLETED"
    return state
