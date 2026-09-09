def job(job_id,node_ref,job_type,dependencies=None,
        priority=0,resources=None,estimated=None,
        deadline=None):
    return {"job_id":job_id,"node_ref":node_ref,
            "job_type":job_type,"dependencies":dependencies or [],
            "priority":priority,"resources":resources or {},
            "estimated":estimated or {},"deadline":deadline}

def ready_jobs(jobs,completed):
    completed=set(completed)
    return [j for j in jobs if all(d in completed for d in j["dependencies"])]
