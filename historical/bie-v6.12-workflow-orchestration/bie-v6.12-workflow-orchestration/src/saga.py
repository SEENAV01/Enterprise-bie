def saga_step(step_id,
              action,
              compensation=None):
    return {"step_id":step_id,
            "action":action,
            "compensation":compensation,
            "status":"PENDING"}

def complete(record):
    out=dict(record); out["status"]="COMPLETED"; return out

def compensate(record):
    out=dict(record); out["status"]="COMPENSATING"; return out
