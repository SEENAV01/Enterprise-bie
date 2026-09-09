def delivery_retry(message_id,attempt,
                  max_attempts=5,backoff_seconds=1):
    return {"message_id":message_id,
            "attempt":attempt,
            "max_attempts":max_attempts,
            "backoff_seconds":backoff_seconds}

def retryable(record):
    return record["attempt"]<record["max_attempts"]
