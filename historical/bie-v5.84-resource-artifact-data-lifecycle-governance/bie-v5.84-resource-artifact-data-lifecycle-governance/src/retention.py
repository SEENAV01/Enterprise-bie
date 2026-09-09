def retention_policy(policy_id,ttl_seconds=None,
                     archive_after_seconds=None,
                     delete_after_archive=False):
    return {"policy_id":policy_id,
            "ttl_seconds":ttl_seconds,
            "archive_after_seconds":archive_after_seconds,
            "delete_after_archive":delete_after_archive}

def retention_action(age_seconds,policy):
    if (policy.get("archive_after_seconds") is not None and
        age_seconds>=policy["archive_after_seconds"]):
        return "ARCHIVE"
    if (policy.get("ttl_seconds") is not None and
        age_seconds>=policy["ttl_seconds"]):
        return "DELETE"
    return "RETAIN"
