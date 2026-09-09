def principal(principal_id,principal_type,
             roles=None,attributes=None,active=True):
    return {"principal_id":principal_id,
            "principal_type":principal_type,
            "roles":roles or [],
            "attributes":attributes or {},
            "active":active}

def service_identity(service_id,scopes=None):
    return principal(service_id,"SERVICE",
                     attributes={"scopes":scopes or []})
