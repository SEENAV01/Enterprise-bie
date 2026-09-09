def optimization_plan(jobs,workers,budget):
    total=sum(j.get("estimated_cost",0) for j in jobs)
    if total<=budget:
        return {"strategy":"RUN_ALL","estimated_cost":total}
    ordered=sorted(jobs,key=lambda j:j.get("estimated_cost",0))
    chosen=[]; cost=0
    for j in ordered:
        c=j.get("estimated_cost",0)
        if cost+c<=budget:
            chosen.append(j); cost+=c
    return {"strategy":"BUDGETED_SELECTION",
            "estimated_cost":cost,
            "deferred":[j["job_id"] for j in jobs if j not in chosen]}
