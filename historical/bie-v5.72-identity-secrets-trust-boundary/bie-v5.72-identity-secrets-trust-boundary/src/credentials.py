def credential_ref(credential_id,scope=None,
                   expires_at=None,rotation_id=None):
    return {"credential_id":credential_id,
            "scope":scope or [],"expires_at":expires_at,
            "rotation_id":rotation_id}

def credential_allows(credential,permission):
    return permission in set(credential.get("scope",[]))
