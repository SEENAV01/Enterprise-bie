from jobs import ready_jobs
from resources import fits,reserve
from critical_path import critical_path

def schedule(jobs,completed=None,resources=None):
    completed=set(completed or [])
    resources=resources or {}
    ordered,memo=critical_path(jobs)
    ready=ready_jobs(jobs,completed)
    rank={jid:i for i,jid in enumerate(ordered)}
    ready=sorted(ready,key=lambda j:(-j["priority"],rank.get(j["job_id"],999999),
                                     -j.get("estimated",{}).get("duration",0)))
    running=[]
    remaining=resources
    for j in ready:
        req=j.get("resources",{})
        if fits(req,remaining):
            running.append(j)
            remaining=reserve(remaining,req)
    return {"ready":[j["job_id"] for j in ready],
            "scheduled":[j["job_id"] for j in running],
            "remaining_resources":remaining,
            "criticality":{j:memo[j] for j in memo}}

def next_wave(jobs,completed,resources):
    return schedule(jobs,completed,resources)
