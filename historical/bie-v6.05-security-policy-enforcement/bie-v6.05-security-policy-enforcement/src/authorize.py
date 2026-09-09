def authorization_request(subject,tenant,
                         action,resource,
                         context=None):
    return {"subject":subject,"tenant":tenant,
            "action":action,"resource":resource,
            "context":context or {}}

def decide(request,roles,
           tenant_match=True):
    if not tenant_match:
        return {"decision":"DENY",
                "reason":"TENANT_ISOLATION"}
    allowed=role_allows(roles,
                        request["action"],
                        request["resource"])
    return {"decision":"ALLOW" if allowed else "DENY",
            "reason":"PERMISSION_MATCH" if allowed
                    else "NO_EXPLICIT_PERMISSION"}
