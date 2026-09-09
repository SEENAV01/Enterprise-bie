def delivery_guarantee(mode="AT_LEAST_ONCE"):
    if mode not in {"AT_MOST_ONCE","AT_LEAST_ONCE","EXACTLY_ONCE"}:
        raise ValueError("INVALID_DELIVERY_GUARANTEE")
    return {"mode":mode}

def retryable(record):
    return record["mode"] in {"AT_LEAST_ONCE","EXACTLY_ONCE"}
