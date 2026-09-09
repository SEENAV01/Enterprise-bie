def compensation_plan(actions):
    return {"actions":list(reversed(actions))}

def compensate(executed_actions):
    return [{"action":a,"mode":"COMPENSATE"} for a in reversed(executed_actions)]
