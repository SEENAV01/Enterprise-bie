def timeout(duration, unit="SECONDS",
            action="CANCEL"):
    if duration <= 0:
        raise ValueError("INVALID_TIMEOUT")
    if action not in {"CANCEL","RETRY","ESCALATE"}:
        raise ValueError("INVALID_TIMEOUT_ACTION")
    return {"duration":duration,"unit":unit,"action":action}

def expired(record, elapsed):
    return elapsed >= record["duration"]
