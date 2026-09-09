def reviewer(reviewer_id,roles,active=True):
    return {"reviewer_id":reviewer_id,
            "roles":roles,"active":active}

def authorized(reviewer_record,required_role):
    if not reviewer_record.get("active",False): return False
    if required_role is None: return True
    return required_role in set(reviewer_record.get("roles",[]))
