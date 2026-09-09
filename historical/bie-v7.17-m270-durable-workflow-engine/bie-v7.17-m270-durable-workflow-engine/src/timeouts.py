def set_timeout(workflow_id, state, deadline):
    return {"workflow_id":workflow_id,"state":state,"deadline":deadline,"status":"ACTIVE"}

def timeout_due(timer, now):
    return timer["status"]=="ACTIVE" and now>=timer["deadline"]

def fire_timeout(timer):
    timer["status"]="FIRED"
    return timer
