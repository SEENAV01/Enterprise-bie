def delivery_policy(mode="AT_LEAST_ONCE",
                   ack_required=True):
    if mode not in {"AT_MOST_ONCE",
                    "AT_LEAST_ONCE",
                    "EXACTLY_ONCE"}:
        raise ValueError("INVALID_DELIVERY_MODE")
    return {"mode":mode,
            "ack_required":ack_required}

def requires_ack(record):
    return record["ack_required"]
