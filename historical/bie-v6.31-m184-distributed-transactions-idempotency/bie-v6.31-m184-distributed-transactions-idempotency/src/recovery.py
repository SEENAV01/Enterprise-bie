def recovery_policy(max_retries=3,
                    backoff_seconds=5):
    if max_retries < 0 or backoff_seconds < 0:
        raise ValueError("INVALID_RECOVERY_POLICY")
    return {"max_retries":max_retries,
            "backoff_seconds":backoff_seconds}

def retry_allowed(policy,attempt):
    return attempt < policy["max_retries"]
