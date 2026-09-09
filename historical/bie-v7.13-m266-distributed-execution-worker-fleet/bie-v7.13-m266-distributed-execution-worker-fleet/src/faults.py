def recover_expired_job(job, lease):
    if lease["status"]!="EXPIRED":
        return {"requeue":False,"job":job}
    job["status"]="QUEUED"
    job["attempt"]+=1
    return {"requeue":True,"job":job}

def isolate_worker(worker):
    worker["status"]="ISOLATED"
    return worker
