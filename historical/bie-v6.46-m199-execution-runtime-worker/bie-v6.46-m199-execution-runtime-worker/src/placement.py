def placement(task_id, worker_id,
             constraints=None, score=None):
    return {"task_id":task_id,"worker_id":worker_id,
            "constraints":constraints or {},
            "score":score,"status":"SELECTED"}

def selected(record):
    return record["status"]=="SELECTED"
