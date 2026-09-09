STATUSES={"IDLE","BUSY","FAILED","DRAINING"}

def worker(worker_id,capabilities=None,status="IDLE"):
    return {"worker_id":worker_id,"capabilities":capabilities or [],
            "status":status,"current_job":None}

def can_run(w,j):
    return w["status"]=="IDLE" and (
        not j["resources"].get("gpu",0) or "gpu" in w["capabilities"]
    )
