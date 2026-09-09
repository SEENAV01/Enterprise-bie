def step(step_id,action,compensation=None,
         timeout_seconds=None,retry_policy=None):
    return {"step_id":step_id,"action":action,
            "compensation":compensation,
            "timeout_seconds":timeout_seconds,
            "retry_policy":retry_policy or {},
            "state":"PENDING"}

def mark(step_record,state):
    out=dict(step_record); out["state"]=state; return out
