SUPPORTED_STATUS = {"QUEUED","RUNNING","SUCCEEDED","FAILED","CANCELLED"}

def render_job(job_id, composition_id, render_profile_id,
               output_path, priority="NORMAL"):
    return {"job_id":job_id,"composition_id":composition_id,
            "render_profile_id":render_profile_id,
            "output_path":output_path,"priority":priority,
            "status":"QUEUED"}

def valid(job):
    return bool(job["job_id"] and job["composition_id"] and
                job["render_profile_id"] and job["output_path"])
