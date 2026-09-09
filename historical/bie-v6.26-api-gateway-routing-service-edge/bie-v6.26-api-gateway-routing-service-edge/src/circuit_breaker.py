def circuit_breaker(name,
                   failure_threshold=5,
                   recovery_timeout=30):
    if failure_threshold < 1 or recovery_timeout <= 0:
        raise ValueError("INVALID_CIRCUIT_POLICY")
    return {"name":name,
            "failure_threshold":failure_threshold,
            "recovery_timeout":recovery_timeout,
            "state":"CLOSED"}

def allows(record):
    return record["state"] in {"CLOSED","HALF_OPEN"}
