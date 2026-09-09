def prerequisite_graph(nodes):
    edges=[]
    for n in nodes:
        for p in n.get("prerequisites",[]):
            edges.append({"from":p,"to":n.get("id") or n.get("concept_id"),
                          "relation":"PREREQUISITE"})
    return edges

def topological_order(nodes,edges):
    ids=[n.get("id") or n.get("concept_id") for n in nodes]
    incoming={i:0 for i in ids}
    outgoing={i:[] for i in ids}
    for e in edges:
        if e["from"] in incoming and e["to"] in incoming:
            incoming[e["to"]]+=1
            outgoing[e["from"]].append(e["to"])
    queue=[i for i in ids if incoming[i]==0]
    order=[]
    while queue:
        x=queue.pop(0); order.append(x)
        for y in outgoing[x]:
            incoming[y]-=1
            if incoming[y]==0: queue.append(y)
    return {"order":order,"has_cycle":len(order)!=len(ids)}
