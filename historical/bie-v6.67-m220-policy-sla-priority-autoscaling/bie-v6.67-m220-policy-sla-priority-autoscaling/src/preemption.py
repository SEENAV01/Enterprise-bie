def choose_preemption(running_jobs,waiting_job):
    if waiting_job.get("priority_class") not in {"CRITICAL","HIGH"}:
        return None
    candidates=[j for j in running_jobs
                if j.get("preemptible",False)
                and j.get("priority_class") not in {"CRITICAL","HIGH"}]
    if not candidates: return None
    return min(candidates,key=lambda j:j.get("priority_class","NORMAL"))
