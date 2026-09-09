def rotation_hook(credential_id,
                  current_version,
                  next_version,
                  rotate_at):
    return {"credential_id":credential_id,
            "current_version":current_version,
            "next_version":next_version,
            "rotate_at":rotate_at,
            "status":"SCHEDULED"}

def rotated(record):
    out=dict(record); out["status"]="ROTATED"; return out
