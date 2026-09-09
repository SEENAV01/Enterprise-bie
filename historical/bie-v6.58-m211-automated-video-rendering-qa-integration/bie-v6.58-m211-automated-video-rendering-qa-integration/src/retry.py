def retry_policy(max_attempts=3, backoff_sec=5,
                 retryable_errors=None):
    return {"max_attempts":max_attempts,"backoff_sec":backoff_sec,
            "retryable_errors":retryable_errors or [
                "TRANSIENT_RENDER_ERROR","WORKER_TIMEOUT"
            ]}

def should_retry(error_code, attempt, policy):
    return attempt < policy["max_attempts"] and error_code in policy["retryable_errors"]
