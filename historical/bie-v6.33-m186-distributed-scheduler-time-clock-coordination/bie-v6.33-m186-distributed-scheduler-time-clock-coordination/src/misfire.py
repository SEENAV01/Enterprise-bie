def misfire_policy(action="SKIP", grace_seconds=0):
    if action not in {"SKIP","RUN_ONCE","CATCH_UP","RESCHEDULE"}:
        raise ValueError("INVALID_MISFIRE_ACTION")
    if grace_seconds < 0:
        raise ValueError("INVALID_GRACE")
    return {"action":action,"grace_seconds":grace_seconds}

def should_run(record,delay_seconds):
    return delay_seconds <= record["grace_seconds"] or record["action"] in {"RUN_ONCE","CATCH_UP"}
