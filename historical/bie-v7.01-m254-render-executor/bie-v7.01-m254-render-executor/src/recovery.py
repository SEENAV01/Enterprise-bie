RETRYABLE={"RENDER_TIMEOUT","TRANSIENT_RENDER_ERROR","WORKER_UNAVAILABLE"}

def classify_failure(error_code):
    return {"code":error_code,
            "retryable":error_code in RETRYABLE,
            "action":"RETRY" if error_code in RETRYABLE else "FAIL_FAST"}

def recovery_plan(failure, max_retries=2):
    c=classify_failure(failure.get("code","UNKNOWN"))
    return {"classification":c,"max_retries":max_retries,
            "next_action":c["action"]}

def validate_recovery(plan):
    return {"valid":plan["max_retries"]>=0,"errors":[] if plan["max_retries"]>=0 else ["INVALID_RETRY_COUNT"]}
