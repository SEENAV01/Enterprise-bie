def reviewer(reviewer_id,roles,capacity=1):
    return {"reviewer_id":reviewer_id,"roles":roles,
            "capacity":capacity,"active":True}

def assign(item,reviewer_record):
    role=item.get("required_role")
    if role and role not in reviewer_record.get("roles",[]):
        raise ValueError("REVIEWER_NOT_ELIGIBLE")
    if not reviewer_record.get("active",False):
        raise ValueError("REVIEWER_INACTIVE")
    out=dict(item); out["reviewer_id"]=reviewer_record["reviewer_id"]
    out["status"]="ASSIGNED"
    return out
