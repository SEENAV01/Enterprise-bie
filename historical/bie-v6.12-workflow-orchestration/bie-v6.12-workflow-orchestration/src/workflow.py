def workflow(workflow_id,name,
             version=1,tenant_id=None,
             initial_state="START"):
    return {"workflow_id":workflow_id,
            "name":name,"version":version,
            "tenant_id":tenant_id,
            "state":initial_state,
            "status":"RUNNING"}

def pause(record):
    out=dict(record); out["status"]="PAUSED"; return out

def resume(record):
    out=dict(record); out["status"]="RUNNING"; return out
