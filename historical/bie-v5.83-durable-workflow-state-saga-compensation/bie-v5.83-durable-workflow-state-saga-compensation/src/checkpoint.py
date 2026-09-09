def checkpoint(workflow_id,state,completed_steps,
              context=None,sequence=0):
    return {"workflow_id":workflow_id,
            "state":state,
            "completed_steps":list(completed_steps),
            "context":context or {},
            "sequence":sequence}

def latest(checkpoints):
    return max(checkpoints,key=lambda x:x.get("sequence",0),default=None)
