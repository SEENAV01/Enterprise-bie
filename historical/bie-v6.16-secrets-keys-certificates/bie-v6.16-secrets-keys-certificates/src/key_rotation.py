def rotation(key_id,current_version,
            next_version,rotate_at):
    return {"key_id":key_id,
            "current_version":current_version,
            "next_version":next_version,
            "rotate_at":rotate_at,
            "status":"SCHEDULED"}

def activate_next(record):
    out=dict(record)
    out["current_version"]=out["next_version"]
    out["status"]="ROTATED"
    return out
