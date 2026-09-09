def retry_policy(max_attempts=3,retryable_errors=None):
    return {"max_attempts":max_attempts,
            "retryable_errors":retryable_errors or [
                "WORKER_LOST","TIMEOUT","TRANSIENT_RESOURCE"
            ]}

def should_retry(j, error, policy):
    return (j["attempt"]+1 < policy["max_attempts"]
            and error in policy["retryable_errors"])
