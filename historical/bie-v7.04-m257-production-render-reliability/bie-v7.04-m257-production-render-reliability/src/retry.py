RETRYABLE={"WORKER_UNAVAILABLE","RENDER_TIMEOUT","TRANSIENT_IO"}

def classify(code):
    return {"code":code,"retryable":code in RETRYABLE}

def retry_job(job, error_code, max_attempts=3):
    c=classify(error_code)
    if c["retryable"] and job["attempt"]+1<max_attempts:
        job["attempt"]+=1; job["status"]="QUEUED"; job["last_error"]=error_code
    else:
        job["status"]="FAILED"
    return job
