def build_course_dag(nodes, edges):
    ids={n["id"] for n in nodes}
    errors=[e for e in edges if e["source"] not in ids or e["target"] not in ids]
    return {"nodes":nodes,"edges":edges,"valid":not errors,"errors":errors}

def topo_order(dag):
    deps={n["id"]:set() for n in dag["nodes"]}
    for e in dag["edges"]: deps[e["target"]].add(e["source"])
    order=[]
    while deps:
        ready=sorted([i for i,v in deps.items() if not v])
        if not ready: return {"valid":False,"order":order,"remaining":sorted(deps)}
        for i in ready:
            order.append(i); deps.pop(i)
            for v in deps.values(): v.discard(i)
    return {"valid":True,"order":order,"remaining":[]}
