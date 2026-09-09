def compensation_plan(workflow_id,steps):
    return {"workflow_id":workflow_id,
            "steps":steps,
            "status":"READY"}

def start(record):
    out=dict(record); out["status"]="RUNNING"; return out
