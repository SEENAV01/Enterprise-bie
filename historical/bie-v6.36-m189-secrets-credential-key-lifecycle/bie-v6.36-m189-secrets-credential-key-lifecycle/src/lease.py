def credential_lease(credential_id, principal_id,
                     issued_at, expires_at):
    return {"credential_id":credential_id,
            "principal_id":principal_id,
            "issued_at":issued_at,
            "expires_at":expires_at,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
