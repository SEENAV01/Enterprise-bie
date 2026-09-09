def retry_policy(max_attempts=3,backoff_seconds=10,
                 retryable_errors=None):
    return {"max_attempts":max_attempts,
            "backoff_seconds":backoff_seconds,
            "retryable_errors":retryable_errors or []}

def should_retry(error,attempt,policy):
    if attempt>=policy.get("max_attempts",3): return False
    allowed=policy.get("retryable_errors",[])
    return not allowed or error in allowed
