def retry_policy(max_attempts=5,
                 backoff_seconds=1):
    return {"max_attempts":max_attempts,
            "backoff_seconds":backoff_seconds}

def retryable(attempt,policy):
    return attempt < policy["max_attempts"]
