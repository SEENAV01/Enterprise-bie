def render_job(job_id,project_id,composition_id,
              output_path,codec="h264",quality=None):
    return {"job_id":job_id,"project_id":project_id,
            "composition_id":composition_id,"output_path":output_path,
            "codec":codec,"quality":quality,"status":"QUEUED"}

def render_result(job_id,status,output_path=None,
                  duration_seconds=None,error=None):
    return {"job_id":job_id,"status":status,
            "output_path":output_path,"duration_seconds":duration_seconds,
            "error":error}
