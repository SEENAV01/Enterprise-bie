def retry_policy(max_attempts=3,
                 backoff_seconds=1,
                 multiplier=2.0):
    return {"max_attempts":max_attempts,
            "backoff_seconds":backoff_seconds,
            "multiplier":multiplier}

def can_retry(attempt,policy):
    return attempt < policy.get("max_attempts",1)

def backoff(attempt,policy):
    return policy.get("backoff_seconds",0) * (
        policy.get("multiplier",1.0) ** max(0,attempt-1))
