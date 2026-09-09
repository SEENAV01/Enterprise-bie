def classify_failure(code):
    retryable={"TIMEOUT","TEMPORARY_UNAVAILABLE","RATE_LIMIT"}
    compensatable={"PARTIAL_COMMIT","DOWNSTREAM_FAILURE","VALIDATION_FAILURE"}
    if code in retryable:return "RETRY"
    if code in compensatable:return "COMPENSATE"
    return "ABORT"

def failure_policy(code,attempt,max_attempts=3):
    action=classify_failure(code)
    if action=="RETRY" and attempt<max_attempts:return {"action":"RETRY","attempt":attempt+1}
    if action=="RETRY":return {"action":"COMPENSATE","attempt":attempt}
    return {"action":action,"attempt":attempt}
