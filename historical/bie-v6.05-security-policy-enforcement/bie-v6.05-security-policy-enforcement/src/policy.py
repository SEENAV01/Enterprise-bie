def security_policy(policy_id,version,
                   default_effect="DENY",
                   rules=None):
    return {"policy_id":policy_id,
            "version":version,
            "default_effect":default_effect,
            "rules":rules or []}

def default_decision(policy):
    return policy.get("default_effect","DENY")
