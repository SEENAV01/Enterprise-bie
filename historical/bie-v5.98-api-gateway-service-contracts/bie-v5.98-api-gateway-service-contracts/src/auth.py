def auth_context(subject,scopes=None,issuer=None,
                credential_id=None):
    return {"subject":subject,"scopes":scopes or [],
            "issuer":issuer,"credential_id":credential_id}

def authorized(context,required_scope):
    return required_scope in context.get("scopes",[])
