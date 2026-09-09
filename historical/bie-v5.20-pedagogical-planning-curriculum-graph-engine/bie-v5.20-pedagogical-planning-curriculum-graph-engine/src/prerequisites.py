def prerequisite_edge(from_concept,to_concept,relation="REQUIRES",
                      strength=1.0,reason=None):
    return {"from_concept":from_concept,"to_concept":to_concept,
            "relation":relation,"strength":strength,"reason":reason}

def topological_order(concepts,edges):
    incoming={c:0 for c in concepts}
    outgoing={c:[] for c in concepts}
    for e in edges:
        a,b=e["from_concept"],e["to_concept"]
        if a in incoming and b in incoming:
            outgoing[a].append(b); incoming[b]+=1
    q=[c for c,v in incoming.items() if v==0]; order=[]
    while q:
        n=q.pop(0); order.append(n)
        for b in outgoing[n]:
            incoming[b]-=1
            if incoming[b]==0: q.append(b)
    return {"order":order,"has_cycle":len(order)!=len(concepts)}
