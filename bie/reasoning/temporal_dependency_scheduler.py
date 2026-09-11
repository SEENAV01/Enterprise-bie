"""RE-TEMP-031 — Produce deterministic order from explicit temporal dependencies."""
def temporal_topological_order(nodes, before_edges):
    ns=tuple(dict.fromkeys(nodes)); graph={n:set() for n in ns}; indeg={n:0 for n in ns}
    for a,b in before_edges:
        if a not in graph or b not in graph: raise ValueError("edge references unknown node")
        if b not in graph[a]: graph[a].add(b); indeg[b]+=1
    ready=sorted(n for n in ns if indeg[n]==0); out=[]
    while ready:
        n=ready.pop(0); out.append(n)
        for m in sorted(graph[n]):
            indeg[m]-=1
            if indeg[m]==0:
                ready.append(m); ready.sort()
    if len(out)!=len(ns): raise ValueError("temporal dependency cycle")
    return tuple(out)
