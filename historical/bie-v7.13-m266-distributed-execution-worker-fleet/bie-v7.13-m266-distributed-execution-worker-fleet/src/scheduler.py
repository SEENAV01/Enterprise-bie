def match_worker(workers, required_capability):
    eligible=[w for w in workers if w["status"]=="HEALTHY"
              and required_capability in w["capabilities"]
              and w["active_jobs"] < w["capacity"]]
    return sorted(eligible,key=lambda w:(w["active_jobs"],w["worker_id"]))[0] if eligible else None

def dispatch(job, worker):
    if worker is None: return {"status":"QUEUED","job_id":job["job_id"]}
    worker["active_jobs"]+=1
    return {"status":"DISPATCHED","job_id":job["job_id"],"worker_id":worker["worker_id"]}
