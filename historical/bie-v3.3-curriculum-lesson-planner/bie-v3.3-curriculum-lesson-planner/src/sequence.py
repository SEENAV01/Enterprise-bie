def topological_order(nodes, dependencies):
    incoming={n:0 for n in nodes}
    outgoing={n:[] for n in nodes}
    for d in dependencies:
        if d["source"] in incoming and d["target"] in incoming:
            outgoing[d["source"]].append(d["target"])
            incoming[d["target"]]+=1
    queue=[n for n,v in incoming.items() if v==0]
    order=[]
    while queue:
        n=queue.pop(0); order.append(n)
        for x in outgoing[n]:
            incoming[x]-=1
            if incoming[x]==0: queue.append(x)
    return order if len(order)==len(nodes) else None

def prioritize(nodes, dependencies, target):
    order=topological_order(nodes,dependencies)
    if order is None: return {"status":"BLOCKED_CYCLE","sequence":[]}
    if target not in order: return {"status":"TARGET_NOT_FOUND","sequence":[]}
    return {"status":"READY","sequence":order[:order.index(target)+1]}
