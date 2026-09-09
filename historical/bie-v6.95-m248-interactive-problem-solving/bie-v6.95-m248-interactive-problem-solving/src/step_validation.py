def validate_step(response, expected, rubric=None):
    rubric=rubric or {}
    if response == expected:
        return {"valid":True,"score":1.0,"reason":"EXACT_MATCH"}
    accepted=rubric.get("accepted",[])
    if response in accepted:
        return {"valid":True,"score":1.0,"reason":"ACCEPTED_VARIANT"}
    return {"valid":False,"score":0.0,"reason":"RETRY"}

def validate_sequence(state):
    return {"passed":0 <= state["current_step"] <= len(state["steps"]),
            "errors":[] if 0 <= state["current_step"] <= len(state["steps"]) else ["INVALID_STEP"]}
