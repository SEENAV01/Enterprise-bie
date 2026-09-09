def retry_decision(job_record,error_class):
    transient={"TIMEOUT","WORKER_LOST","RATE_LIMIT","TEMPORARY_IO"}
    attempts=job_record.get("attempts",0)
    max_attempts=job_record.get("max_attempts",3)
    if error_class in transient and attempts<max_attempts:
        return {"retry":True,"reason":"TRANSIENT"}
    return {"retry":False,"reason":"PERMANENT_OR_EXHAUSTED"}

def backoff_seconds(attempt,base=2,max_seconds=300):
    return min(max_seconds,base**max(0,attempt-1))
