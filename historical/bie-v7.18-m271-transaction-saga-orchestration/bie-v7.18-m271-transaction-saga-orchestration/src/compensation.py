def compensation_for(step):
    return step.get("compensation")

def compensate_saga(saga, failed_step=None):
    actions=[]
    for step_id in reversed(saga["completed"]):
        step=next(s for s in saga["steps"] if s["id"]==step_id)
        action=compensation_for(step)
        if action: actions.append({"step_id":step_id,"action":action})
        saga["compensated"].append(step_id)
    saga["status"]="COMPENSATED"
    return {"saga":saga,"actions":actions,"failed_step":failed_step}
