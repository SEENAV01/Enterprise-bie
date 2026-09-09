def auth_handoff(mode="BEARER",
                identity_ref=None,
                scopes=None):
    if mode not in {"BEARER","API_KEY","MTLS","SESSION"}:
        raise ValueError("INVALID_AUTH_MODE")
    return {"mode":mode,"identity_ref":identity_ref,
            "scopes":scopes or []}

def authorized(record,required_scope=None):
    return required_scope is None or required_scope in record["scopes"]
