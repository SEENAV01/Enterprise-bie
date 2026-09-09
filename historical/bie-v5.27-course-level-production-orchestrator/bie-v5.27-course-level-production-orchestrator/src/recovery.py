def failure_record(job_id,stage,error,retryable=True):
    return {"job_id":job_id,"stage":stage,"error":error,
            "retryable":retryable}

def recoverable_failures(failures):
    return [f for f in failures if f.get("retryable")]
