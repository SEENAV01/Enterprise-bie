def rotation_plan(key_id,current_version,
                  next_version_id, activate_at=None):
    return {"key_id":key_id,
            "current_version":current_version,
            "next_version":next_version_id,
            "activate_at":activate_at,
            "status":"PLANNED"}

def activate(record):
    out=dict(record); out["status"]="ACTIVE"; return out
