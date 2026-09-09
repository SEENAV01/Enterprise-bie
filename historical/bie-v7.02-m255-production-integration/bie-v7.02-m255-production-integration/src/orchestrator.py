def create_render_run(run_id, composition_id):
    return {"run_id":run_id,"composition_id":composition_id,"status":"CREATED",
            "events":[],"attempt":0}

def transition(run,state,event=None):
    allowed={"CREATED":{"VALIDATING"},"VALIDATING":{"READY","FAILED"},
             "READY":{"RENDERING"},"RENDERING":{"SUCCEEDED","FAILED"},
             "FAILED":{"RETRYING","ABORTED"},"RETRYING":{"RENDERING"},
             "SUCCEEDED":{},"ABORTED":{}}
    if state not in allowed.get(run["status"],set()):
        raise ValueError("INVALID_RUN_TRANSITION")
    run["status"]=state
    if event: run["events"].append(event)
    if state=="RENDERING": run["attempt"]+=1
    return run

def orchestrate(run):
    transition(run,"VALIDATING",{"type":"VALIDATION_STARTED"})
    transition(run,"READY",{"type":"VALIDATION_PASSED"})
    transition(run,"RENDERING",{"type":"RENDER_STARTED"})
    transition(run,"SUCCEEDED",{"type":"RENDER_FINISHED"})
    return run
