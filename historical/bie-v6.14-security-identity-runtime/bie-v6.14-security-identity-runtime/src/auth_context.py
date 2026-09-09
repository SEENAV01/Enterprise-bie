def auth_context(subject_id,issuer,
                 tenant_id=None,scopes=None,
                 auth_method="TOKEN"):
    return {"subject_id":subject_id,
            "issuer":issuer,
            "tenant_id":tenant_id,
            "scopes":scopes or [],
            "auth_method":auth_method}

def authenticated(record):
    return bool(record.get("subject_id") and
                record.get("issuer"))
