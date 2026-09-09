def dead_letter(evt,reason,attempts):
    return {"event":evt,"reason":reason,
            "attempts":attempts,"state":"DEAD_LETTERED"}

def retryable(attempt,max_attempts):
    return attempt < max_attempts
