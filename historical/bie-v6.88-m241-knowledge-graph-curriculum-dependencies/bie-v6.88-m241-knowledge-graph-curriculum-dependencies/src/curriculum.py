from prerequisites import prerequisite_map

def dependency_order(nodes,edges):
    ids=[n["node_id"] for n in nodes]
    req=prerequisite_map(edges)
    remaining=set(ids); order=[]
    while remaining:
        ready=[x for x in remaining if all(r not in remaining for r in req.get(x,[]))]
        if not ready:return {"valid":False,"order":order,"remaining":sorted(remaining)}
        ready.sort(); order.extend(ready); remaining-=set(ready)
    return {"valid":True,"order":order,"remaining":[]}

def validate_curriculum(nodes,edges):
    return dependency_order(nodes,edges)
