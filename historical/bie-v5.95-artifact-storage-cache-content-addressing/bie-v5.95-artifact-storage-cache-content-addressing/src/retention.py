def retention_policy(policy_id,max_age=None,
                    keep_versions=None,tier=None):
    return {"policy_id":policy_id,"max_age":max_age,
            "keep_versions":keep_versions,"tier":tier}

def retention_decision(policy,age,version_count):
    if policy.get("max_age") is not None and age>policy["max_age"]:
        return "EXPIRE"
    if policy.get("keep_versions") is not None and version_count>policy["keep_versions"]:
        return "PRUNE_OLD_VERSIONS"
    return "KEEP"
