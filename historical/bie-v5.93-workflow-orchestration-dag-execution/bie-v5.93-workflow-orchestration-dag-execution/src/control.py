def control_request(workflow_id,action,reason=None):
    allowed={"PAUSE","RESUME","CANCEL"}
    if action not in allowed:
        raise ValueError("INVALID_WORKFLOW_CONTROL")
    return {"workflow_id":workflow_id,
            "action":action,"reason":reason}

def apply_control(execution_record,request):
    action=request["action"]
    if action=="PAUSE":
        return transition(execution_record,"PAUSED")
    if action=="RESUME":
        return transition(execution_record,"RUNNING")
    if action=="CANCEL":
        out=transition(execution_record,"CANCELLED")
        out["cancelled"]=True
        return out

def transition(record,status):
    out=dict(record); out["status"]=status
    return out
