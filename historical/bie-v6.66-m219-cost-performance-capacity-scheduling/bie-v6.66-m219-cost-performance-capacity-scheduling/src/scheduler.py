def score(job,worker,weights=None):
    w=weights or {"queue":1.0,"cost":1.0,"gpu":1.0}
    return (w["queue"]*job.get("queue_seconds",0)
            +w["cost"]*job.get("estimated_cost",0)
            +w["gpu"]*worker.get("gpu_load",0))

def rank_jobs(jobs,worker,weights=None):
    return sorted(jobs,key=lambda j:score(j,worker,weights))
