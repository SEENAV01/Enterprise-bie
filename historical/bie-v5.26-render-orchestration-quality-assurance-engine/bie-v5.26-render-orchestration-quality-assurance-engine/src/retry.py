def retry_policy(max_attempts=3,backoff_seconds=5,
                 retryable_errors=None):
    return {"max_attempts":max_attempts,"backoff_seconds":backoff_seconds,
            "retryable_errors":retryable_errors or
              ["TRANSIENT_RENDER_ERROR","RESOURCE_UNAVAILABLE"]}

def next_attempt(attempt,max_attempts):
    return {"retry":attempt<max_attempts,"attempt":attempt+1}
