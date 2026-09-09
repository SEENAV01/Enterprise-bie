def gateway_retry(max_attempts=2,
                  backoff="EXPONENTIAL",
                  retry_on=None):
    if max_attempts < 1:
        raise ValueError("INVALID_MAX_ATTEMPTS")
    return {"max_attempts":max_attempts,
            "backoff":backoff,
            "retry_on":retry_on or
              ["502","503","504"]}

def should_retry(record,status,attempt):
    return attempt < record["max_attempts"] and status in record["retry_on"]
