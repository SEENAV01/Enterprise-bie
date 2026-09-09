def resource_fit(job, available):
    req=job["payload"].get("resources",{"cpu":1,"ram_mb":1024})
    return req["cpu"]<=available["cpu"] and req["ram_mb"]<=available["ram_mb"]

def schedule(queue, available, concurrency):
    selected=[]; remaining=[]
    for job in queue:
        if len(selected)<concurrency and resource_fit(job,available):
            selected.append(job)
        else: remaining.append(job)
    return {"selected":selected,"remaining":remaining}
