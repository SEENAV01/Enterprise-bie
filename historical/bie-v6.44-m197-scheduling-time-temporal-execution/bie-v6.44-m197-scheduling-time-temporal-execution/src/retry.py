def temporal_retry(max_attempts=3, delay=1,
                   unit="SECONDS", backoff="EXPONENTIAL"):
    if max_attempts < 1:
        raise ValueError("INVALID_MAX_ATTEMPTS")
    if backoff not in {"FIXED","LINEAR","EXPONENTIAL"}:
        raise ValueError("INVALID_BACKOFF")
    return {"max_attempts":max_attempts,"delay":delay,
            "unit":unit,"backoff":backoff}

def allowed(record, attempt):
    return attempt <= record["max_attempts"]
