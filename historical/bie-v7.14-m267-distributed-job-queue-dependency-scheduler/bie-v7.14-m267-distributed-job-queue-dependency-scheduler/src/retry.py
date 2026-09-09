def retry_policy(attempt, max_attempts=3, backoff_base=2):
    if attempt>=max_attempts: return {"retry":False,"delay":None}
    return {"retry":True,"delay":backoff_base**attempt}

def mark_failure(job, error_code, max_attempts=3):
    job["attempt"]=job.get("attempt",0)+1; job["last_error"]=error_code
    p=retry_policy(job["attempt"],max_attempts)
    job["status"]="RETRY_WAIT" if p["retry"] else "FAILED"
    return {**job,"retry_policy":p}
