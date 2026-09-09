def queue(name,
          visibility_timeout=30,
          max_attempts=5):
    if visibility_timeout <= 0 or max_attempts < 1:
        raise ValueError("INVALID_QUEUE_POLICY")
    return {"name":name,
            "visibility_timeout":visibility_timeout,
            "max_attempts":max_attempts}

def retryable(record,attempt):
    return attempt < record["max_attempts"]
