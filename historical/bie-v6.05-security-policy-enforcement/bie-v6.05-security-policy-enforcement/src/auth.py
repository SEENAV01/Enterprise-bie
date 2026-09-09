def authentication_context(identity_record,
                            authenticated_at,
                            method="TOKEN"):
    return {"identity":identity_record,
            "authenticated_at":authenticated_at,
            "method":method,
            "authenticated":True}

def authenticated(context):
    return bool(context.get("authenticated"))
