def timeout(step_record,elapsed_seconds):
    limit=step_record.get("timeout_seconds")
    return limit is not None and elapsed_seconds>=limit

def timeout_action(step_record):
    return "COMPENSATE" if step_record.get("compensation") else "FAIL"
