from __future__ import annotations
from collections import deque

def prerequisite_depth(nodes:set[str], edges:list[tuple[str,str]]) -> dict[str,int]:
    incoming={n:set() for n in nodes}; outgoing={n:set() for n in nodes}
    for a,b in edges:
        if a not in nodes or b not in nodes: raise ValueError("unknown node")
        incoming[b].add(a); outgoing[a].add(b)
    q=deque(sorted(n for n in nodes if not incoming[n]))
    depth={n:0 for n in q}; seen=0
    indeg={n:len(incoming[n]) for n in nodes}
    while q:
        n=q.popleft(); seen+=1
        for m in sorted(outgoing[n]):
            depth[m]=max(depth.get(m,0),depth[n]+1)
            indeg[m]-=1
            if indeg[m]==0: q.append(m)
    if seen != len(nodes): raise ValueError("graph contains cycle")
    return depth
