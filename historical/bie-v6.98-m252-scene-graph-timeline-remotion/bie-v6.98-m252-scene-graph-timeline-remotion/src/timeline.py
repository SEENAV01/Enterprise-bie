def resolve_timeline(events):
    ordered=sorted(events,key=lambda e:(e.get("start_frame",0),e["id"]))
    errors=[]
    for a,b in zip(ordered,ordered[1:]):
        if a.get("end_frame",0)>b.get("start_frame",0) and a.get("exclusive",False):
            errors.append(f"OVERLAP:{a['id']}:{b['id']}")
    return {"valid":not errors,"events":ordered,"errors":errors}

def dependency_order(events,dependencies):
    remaining={e["id"]:e for e in events}; order=[]
    while remaining:
        ready=[i for i in remaining if all(d not in remaining for d in dependencies.get(i,[]))]
        if not ready: return {"valid":False,"order":order,"remaining":sorted(remaining)}
        for i in sorted(ready): order.append(i); remaining.pop(i)
    return {"valid":True,"order":order,"remaining":[]}
