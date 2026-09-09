SEMANTICS={"AT_MOST_ONCE",
          "AT_LEAST_ONCE","EFFECTIVELY_ONCE"}

def delivery_policy(mode,
                    ack_timeout_seconds=30,
                    max_attempts=5):
    if mode not in SEMANTICS:
        raise ValueError("INVALID_DELIVERY_SEMANTICS")
    return {"mode":mode,
            "ack_timeout_seconds":ack_timeout_seconds,
            "max_attempts":max_attempts}

def retryable(record,attempt):
    return attempt < record["max_attempts"]
