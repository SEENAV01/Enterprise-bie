def rotation_plan(material_id,current_version,
                  next_version,created_at,
                  overlap=True):
    return {"material_id":material_id,
            "current_version":current_version,
            "next_version":next_version,
            "created_at":created_at,
            "overlap":overlap,"status":"PLANNED"}

def complete_rotation(plan):
    out=dict(plan)
    out["current_version"]=plan["next_version"]
    out["status"]="COMPLETED"
    return out
