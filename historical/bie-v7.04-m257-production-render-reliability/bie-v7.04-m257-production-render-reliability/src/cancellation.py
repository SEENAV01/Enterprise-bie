def cancel(job, reason="USER_REQUEST"):
    if job["status"] in {"QUEUED","RUNNING","PAUSED"}:
        job["status"]="CANCELLED"; job["cancel_reason"]=reason
    return job

def can_resume(job):
    return bool(job.get("checkpoint")) and job.get("status") in {"FAILED","CANCELLED","PAUSED"}
