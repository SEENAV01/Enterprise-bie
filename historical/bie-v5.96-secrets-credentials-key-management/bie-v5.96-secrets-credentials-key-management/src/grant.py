def access_grant(grant_id,secret_ref,scope_ref,
                issued_at,expires_at,subject):
    return {"grant_id":grant_id,
            "secret":secret_ref,"scope":scope_ref,
            "issued_at":issued_at,"expires_at":expires_at,
            "subject":subject,"status":"ACTIVE"}

def expired(grant,now):
    return now>=grant["expires_at"]

def revoke(grant):
    out=dict(grant); out["status"]="REVOKED"
    return out
