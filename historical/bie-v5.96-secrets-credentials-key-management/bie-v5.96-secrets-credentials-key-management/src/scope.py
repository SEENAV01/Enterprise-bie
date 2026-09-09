def credential_scope(scope_id,service,
                    actions=None,resources=None,
                    audience=None):
    return {"scope_id":scope_id,"service":service,
            "actions":actions or [],
            "resources":resources or [],
            "audience":audience}

def scope_allows(scope,service,action,resource=None):
    if scope.get("service")!=service: return False
    if action not in scope.get("actions",[]): return False
    resources=scope.get("resources",[])
    return resource is None or resource in resources
