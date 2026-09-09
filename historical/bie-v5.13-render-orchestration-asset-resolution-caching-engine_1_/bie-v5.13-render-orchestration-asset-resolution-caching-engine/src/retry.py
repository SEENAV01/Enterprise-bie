def retry_policy(max_attempts=3):
    return {"max_attempts":max_attempts,
            "retry_transient_errors":True,
            "do_not_retry_validation_errors":True}

def classify_render_error(error_code):
    validation={"INVALID_SCENE","MISSING_ASSET","INVALID_TIMELINE"}
    transient={"TIMEOUT","WORKER_FAILURE","TEMPORARY_IO"}
    if error_code in validation: return "VALIDATION"
    if error_code in transient: return "TRANSIENT"
    return "UNKNOWN"
