def retry_policy(max_attempts=5,
                backoff="EXPONENTIAL",
                initial_delay=1):
    if max_attempts < 1 or initial_delay < 0:
        raise ValueError("INVALID_RETRY_POLICY")
    if backoff not in {"FIXED","LINEAR","EXPONENTIAL"}:
        raise ValueError("INVALID_BACKOFF")
    return {"max_attempts":max_attempts,
            "backoff":backoff,
            "initial_delay":initial_delay}

def delay(record,attempt):
    if record["backoff"]=="FIXED":
        return record["initial_delay"]
    if record["backoff"]=="LINEAR":
        return record["initial_delay"]*attempt
    return record["initial_delay"]*(2**max(0,attempt-1))
