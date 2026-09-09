def attempt(attempt_id, task_id, attempt_number=1,
            worker_id=None):
    if attempt_number < 1:
        raise ValueError("INVALID_ATTEMPT_NUMBER")
    return {"attempt_id":attempt_id,"task_id":task_id,
            "attempt_number":attempt_number,
            "worker_id":worker_id,"status":"RUNNING"}

def running(record):
    return record["status"]=="RUNNING"
