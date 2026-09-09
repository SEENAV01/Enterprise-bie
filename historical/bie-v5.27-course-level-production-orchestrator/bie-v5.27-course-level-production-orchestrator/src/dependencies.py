def dependency_graph(nodes,edges):
    incoming={n:0 for n in nodes}; outgoing={n:[] for n in nodes}
    for a,b in edges:
        if a in incoming and b in incoming:
            outgoing[a].append(b); incoming[b]+=1
    q=[n for n,v in incoming.items() if v==0]; order=[]
    while q:
        n=q.pop(0); order.append(n)
        for b in outgoing[n]:
            incoming[b]-=1
            if incoming[b]==0:q.append(b)
    return {"order":order,"has_cycle":len(order)!=len(nodes)}
