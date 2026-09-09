def rate_limit(key,limit,window_seconds,
               algorithm="TOKEN_BUCKET"):
    if limit < 1 or window_seconds < 1:
        raise ValueError("INVALID_RATE_LIMIT")
    if algorithm not in {"TOKEN_BUCKET","FIXED_WINDOW","SLIDING_WINDOW"}:
        raise ValueError("INVALID_RATE_LIMIT_ALGORITHM")
    return {"key":key,"limit":limit,
            "window_seconds":window_seconds,
            "algorithm":algorithm}

def within(record,requests):
    return requests <= record["limit"]
