def decision(policy,context):
    # Reference evaluator: explicit boolean rule.
    rule=policy.get("allow",False)
    if callable(rule):
        allowed=bool(rule(context))
    else:
        allowed=bool(rule)
    return {"allowed":allowed,
            "policy_id":policy.get("policy_id"),
            "policy_version":policy.get("version")}
