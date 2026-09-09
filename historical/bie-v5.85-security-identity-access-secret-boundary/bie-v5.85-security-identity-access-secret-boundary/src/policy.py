def access_policy(resource_type,action,
                 allowed_roles=None,required_scope=None,
                 effect="DENY"):
    return {"resource_type":resource_type,"action":action,
            "allowed_roles":allowed_roles or [],
            "required_scope":required_scope,
            "effect":effect}

def security_policy():
    return {
      "deny_by_default":True,
      "least_privilege":True,
      "identity_is_distinct_from_permission":True,
      "secrets_are_referenced_not_embedded":True,
      "privileged_actions_require_explicit_policy":True
    }
