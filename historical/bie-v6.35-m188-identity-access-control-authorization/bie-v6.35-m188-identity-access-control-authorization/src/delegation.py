def delegation(delegator, delegatee, scope,
                expires_at=None):
    return {"delegator":delegator,"delegatee":delegatee,
            "scope":scope,"expires_at":expires_at,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
