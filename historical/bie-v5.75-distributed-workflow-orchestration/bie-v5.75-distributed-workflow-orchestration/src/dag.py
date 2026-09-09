def validate_dag(jobs):
    ids={j["job_id"] for j in jobs}
    edges={j["job_id"]:set(j.get("depends_on",[])) for j in jobs}
    if any(d not in ids for ds in edges.values() for d in ds):
        return {"valid":False,"reason":"MISSING_DEPENDENCY"}
    visiting=set(); visited=set()
    def visit(n):
        if n in visiting: return False
        if n in visited: return True
        visiting.add(n)
        for d in edges[n]:
            if not visit(d): return False
        visiting.remove(n); visited.add(n); return True
    ok=all(visit(n) for n in edges)
    return {"valid":ok,"reason":"OK" if ok else "CYCLE"}

def topological_order(jobs):
    remaining={j["job_id"]:set(j.get("depends_on",[])) for j in jobs}
    order=[]
    while remaining:
        ready=sorted(k for k,v in remaining.items() if not v)
        if not ready: raise ValueError("CYCLE")
        order.extend(ready)
        for k in ready: remaining.pop(k)
        for deps in remaining.values(): deps.difference_update(ready)
    return order
