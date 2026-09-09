def role(role_id, permissions=None, parents=None):
    return {"role_id":role_id,"permissions":permissions or [],
            "parents":parents or [],"status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
