def topological_order(nodes,edges):
    incoming={n:0 for n in nodes}
    outgoing={n:[] for n in nodes}
    for e in edges:
        a,b=e["prerequisite"],e["dependent"]
        incoming[b]=incoming.get(b,0)+1
        outgoing.setdefault(a,[]).append(b)
        incoming.setdefault(a,0)
    ready=sorted([n for n,v in incoming.items() if v==0])
    result=[]
    while ready:
        n=ready.pop(0); result.append(n)
        for nxt in outgoing.get(n,[]):
            incoming[nxt]-=1
            if incoming[nxt]==0: ready.append(nxt); ready.sort()
    if len(result)!=len(incoming):
        raise ValueError("KNOWLEDGE_GRAPH_CYCLE")
    return result
