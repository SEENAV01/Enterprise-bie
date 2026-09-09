SUPPORTED_FAILURES = {
    "VISUAL","AUDIO","SYNC","CAPTION","RENDER","CONTENT","LAYOUT","UNKNOWN"
}

def failure(failure_id, failure_type, severity, target_ref,
           qa_check_id, message, observed=None, expected=None):
    if failure_type not in SUPPORTED_FAILURES:
        raise ValueError("UNSUPPORTED_FAILURE_TYPE")
    if severity not in {"LOW","MEDIUM","HIGH","CRITICAL"}:
        raise ValueError("INVALID_FAILURE_SEVERITY")
    return {"failure_id":failure_id,"failure_type":failure_type,
            "severity":severity,"target_ref":target_ref,
            "qa_check_id":qa_check_id,"message":message,
            "observed":observed,"expected":expected}

def valid(f):
    return bool(f["failure_id"] and f["target_ref"] and f["qa_check_id"])
