def prerequisite_order(nodes, edges):
    incoming={n:0 for n in nodes}
    outgoing={n:[] for n in nodes}
    for e in edges:
        if e["source"] in incoming and e["target"] in incoming:
            outgoing[e["source"]].append(e["target"])
            incoming[e["target"]]+=1
    q=[n for n,v in incoming.items() if v==0]
    order=[]
    while q:
        n=q.pop(0); order.append(n)
        for x in outgoing[n]:
            incoming[x]-=1
            if incoming[x]==0:q.append(x)
    if len(order)!=len(nodes):
        return {"status":"BLOCKED_CYCLE","order":[]}
    return {"status":"READY","order":order}
