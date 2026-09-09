def auth_context(principal_id,method,
                 session_id=None,claims=None):
    return {"principal_id":principal_id,
            "method":method,
            "session_id":session_id,
            "claims":claims or {}}

def authenticated(context):
    return bool(context and context.get("principal_id")
                and context.get("method"))
