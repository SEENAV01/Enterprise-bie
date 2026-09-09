def prerequisite_map(edges):
    out={}
    for e in edges:
        if e.get("relation")=="PREREQUISITE":
            out.setdefault(e["target"],[]).append(e["source"])
    return out

def find_cycle(nodes,edges):
    adj={n["node_id"]:[] for n in nodes}
    for e in edges:
        if e.get("relation")=="PREREQUISITE": adj[e["source"]].append(e["target"])
    visiting=set(); visited=set()
    def dfs(x):
        if x in visiting:return True
        if x in visited:return False
        visiting.add(x)
        if any(dfs(y) for y in adj.get(x,[])):return True
        visiting.remove(x); visited.add(x); return False
    return any(dfs(n) for n in adj)

def validate_prerequisites(nodes,edges):
    return {"passed":not find_cycle(nodes,edges),
            "cycle_detected":find_cycle(nodes,edges)}
