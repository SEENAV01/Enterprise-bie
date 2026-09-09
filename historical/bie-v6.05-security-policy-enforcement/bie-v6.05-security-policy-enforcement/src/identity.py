def identity(subject_id,tenant_id,
             identity_type="USER",
             roles=None,claims=None):
    return {"subject_id":subject_id,
            "tenant_id":tenant_id,
            "identity_type":identity_type,
            "roles":roles or [],
            "claims":claims or {}}

def service_identity(service_id,tenant_id=None,
                     claims=None):
    return identity(service_id,tenant_id,
                    "SERVICE",[],claims)
