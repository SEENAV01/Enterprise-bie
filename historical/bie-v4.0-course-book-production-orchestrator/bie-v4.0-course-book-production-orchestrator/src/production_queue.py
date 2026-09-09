def build_production_queue(chapters, graph):
    indegree={n:0 for n in graph["nodes"]}
    outgoing={n:[] for n in graph["nodes"]}
    for e in graph["edges"]:
        outgoing[e["source"]].append(e["target"])
        indegree[e["target"]]+=1
    queue=[n for n,v in indegree.items() if v==0]
    order=[]
    while queue:
        n=queue.pop(0); order.append(n)
        for x in outgoing[n]:
            indegree[x]-=1
            if indegree[x]==0: queue.append(x)
    if len(order)!=len(indegree):
        return {"status":"BLOCKED_CYCLIC_DEPENDENCY","lesson_order":[]}
    return {"status":"READY","lesson_order":order}
