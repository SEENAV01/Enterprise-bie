def dependency(source,target,relation="AFTER",condition=None):
    return {"source":source,"target":target,"relation":relation,
            "condition":condition}

def topological_order(ids,dependencies):
    incoming={x:0 for x in ids}
    children={x:[] for x in ids}
    for d in dependencies:
        a,b=d["source"],d["target"]
        if a in children and b in incoming:
            children[a].append(b); incoming[b]+=1
    q=[x for x,v in incoming.items() if v==0]
    order=[]
    while q:
        x=q.pop(0); order.append(x)
        for y in children[x]:
            incoming[y]-=1
            if incoming[y]==0:q.append(y)
    return order, len(order)!=len(ids)
