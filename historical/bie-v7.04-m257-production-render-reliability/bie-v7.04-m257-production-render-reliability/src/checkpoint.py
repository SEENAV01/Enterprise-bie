def save_checkpoint(job, frame):
    job["checkpoint"]={"frame":frame,"attempt":job["attempt"]}
    return job

def resume_command(job):
    frame=(job.get("checkpoint") or {}).get("frame",0)
    return {"job_id":job["job_id"],"resume_from_frame":frame}

def clear_checkpoint(job):
    job["checkpoint"]=None
    return job
