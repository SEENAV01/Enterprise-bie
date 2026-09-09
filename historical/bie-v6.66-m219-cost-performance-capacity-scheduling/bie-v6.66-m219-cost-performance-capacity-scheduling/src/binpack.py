def can_fit(job,capacity,used):
    return all(used.get(k,0)+job.get(k,0)<=capacity.get(k,0)
               for k in ("cpu","memory","gpu"))

def pack(jobs,capacity):
    used={"cpu":0,"memory":0,"gpu":0}; selected=[]; deferred=[]
    for j in sorted(jobs,key=lambda x:x.get("estimated_cost",0),reverse=True):
        if can_fit(j,capacity,used):
            selected.append(j)
            for k in used: used[k]+=j.get(k,0)
        else: deferred.append(j)
    return {"selected":selected,"deferred":deferred,"used":used}
