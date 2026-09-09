from step_validation import validate_step
from dynamic_hints import next_hint_level,dynamic_hint

def process_turn(state, response, expected, step_text):
    result=validate_step(response,expected)
    if result["valid"]:
        state["responses"].append({"step":state["current_step"],"response":response,"result":result})
        state["current_step"] += 1
        state["hint_level"]="CONCEPT"
        action="ADVANCE"
    else:
        state["responses"].append({"step":state["current_step"],"response":response,"result":result})
        state["hint_level"]=next_hint_level(state["hint_level"],result)
        action="HINT"
    if state["current_step"]>=len(state["steps"]): state["status"]="COMPLETED"
    return {"state":state,"validation":result,"action":action,
            "hint":None if action=="ADVANCE" else dynamic_hint(state["hint_level"],step_text)}

def session_summary(state):
    return {"problem_id":state["problem_id"],"status":state["status"],
            "current_step":state["current_step"],"total_steps":len(state["steps"]),
            "responses":len(state["responses"])}
