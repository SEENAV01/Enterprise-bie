def create_inference_job(job_id, model, prompt, estimated_cost=0.0, estimated_latency=0):
    return {"job_id":job_id,"model_id":model["model_id"],"model_version":model["version"],
            "prompt":prompt,"estimated_cost":estimated_cost,
            "estimated_latency":estimated_latency,"status":"QUEUED","attempt":0}

def start_job(job):
    job["status"]="RUNNING"; job["attempt"]+=1
    return job

def complete_job(job, output):
    job["status"]="COMPLETED"; job["output"]=output
    return job
