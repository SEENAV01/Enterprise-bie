def task(task_id, job_id, payload,
         dependencies=None, timeout=None):
    return {"task_id":task_id,"job_id":job_id,
            "payload":payload,
            "dependencies":dependencies or [],
            "timeout":timeout,"status":"PENDING"}

def runnable(record, completed=None):
    return not (set(record["dependencies"])-set(completed or []))
