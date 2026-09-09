from capability import satisfies,resource_satisfies

def eligible_workers(workers,requirements=None,resources=None):
    requirements=requirements or []
    resources=resources or {}
    return [w for w in workers
            if w.get("status") in {"READY","REGISTERED"}
            and satisfies(w,requirements)
            and resource_satisfies(w,resources)]

def dispatch(task_id,worker_id,requirements=None,
             resources=None):
    return {"task_id":task_id,"worker_id":worker_id,
            "requirements":requirements or [],
            "resources":resources or {},
            "status":"DISPATCHED"}
