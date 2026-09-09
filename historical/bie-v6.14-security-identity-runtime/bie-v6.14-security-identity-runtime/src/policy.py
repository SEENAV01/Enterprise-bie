def authorization_policy(resource,
                        action,subjects=None,
                        scopes=None,tenant_bound=True):
    return {"resource":resource,
            "action":action,
            "subjects":subjects or [],
            "scopes":scopes or [],
            "tenant_bound":tenant_bound}

def allows(policy,subject=None,scope=None):
    subject_ok=(not policy["subjects"] or
                subject in policy["subjects"])
    scope_ok=(not policy["scopes"] or
              scope in policy["scopes"])
    return subject_ok and scope_ok
