def retry_policy(max_attempts=3, backoff_ms=1000,
                multiplier=2.0, max_backoff_ms=60000):
    if max_attempts < 1:
        raise ValueError("INVALID_MAX_ATTEMPTS")
    return {"max_attempts":max_attempts,
            "backoff_ms":backoff_ms,
            "multiplier":multiplier,
            "max_backoff_ms":max_backoff_ms}

def allowed(record, attempt):
    return attempt <= record["max_attempts"]
