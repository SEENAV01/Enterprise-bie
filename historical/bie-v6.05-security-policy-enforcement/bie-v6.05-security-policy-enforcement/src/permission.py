def permission(action,resource,
              effect="ALLOW",
              conditions=None):
    return {"action":action,"resource":resource,
            "effect":effect,
            "conditions":conditions or {}}

def matches(rule,action,resource):
    return (rule.get("action")==action and
            rule.get("resource")==resource)
