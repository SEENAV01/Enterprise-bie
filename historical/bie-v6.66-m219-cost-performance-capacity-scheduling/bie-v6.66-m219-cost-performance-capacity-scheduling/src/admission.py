def admit(job,capacity,quota):
    requested=job.get("estimated_cost",0)
    if requested>quota.get("remaining_cost",0):
        return {"admitted":False,"reason":"COST_QUOTA"}
    if not all(job.get(k,0)<=capacity.get(k,0)
               for k in ("cpu","memory","gpu")):
        return {"admitted":False,"reason":"RESOURCE_CAPACITY"}
    return {"admitted":True,"reason":"OK"}
