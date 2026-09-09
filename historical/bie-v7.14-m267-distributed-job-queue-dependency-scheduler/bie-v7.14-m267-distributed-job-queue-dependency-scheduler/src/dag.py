def validate_dag(nodes, edges):
    ids={n["id"] for n in nodes}; indegree={i:0 for i in ids}; adj={i:[] for i in ids}
    errors=[]
    for e in edges:
        if e["source"] not in ids or e["target"] not in ids: errors.append("DAG_UNKNOWN_NODE"); continue
        adj[e["source"]].append(e["target"]); indegree[e["target"]]+=1
    q=[i for i,v in indegree.items() if v==0]; seen=0
    while q:
        n=q.pop(); seen+=1
        for x in adj[n]:
            indegree[x]-=1
            if indegree[x]==0:q.append(x)
    if seen!=len(ids): errors.append("DAG_CYCLE")
    return {"valid":not errors,"errors":errors}

def ready_nodes(nodes, edges, completed):
    deps={n["id"]:set() for n in nodes}
    for e in edges: deps.setdefault(e["target"],set()).add(e["source"])
    return [n["id"] for n in nodes if n["id"] not in completed and deps[n["id"]] <= set(completed)]
