from __future__ import annotations
import heapq

def teaching_order(nodes:set[str], edges:list[tuple[str,str]], priority:dict[str,float]|None=None)->list[str]:
    priority=priority or {}
    incoming={n:0 for n in nodes}; outgoing={n:set() for n in nodes}
    for a,b in edges:
        if a not in nodes or b not in nodes: raise ValueError("unknown node")
        if a==b: raise ValueError("self-loop")
        if b not in outgoing[a]:
            outgoing[a].add(b); incoming[b]+=1
    ready=[(-priority.get(n,0.0),n) for n in nodes if incoming[n]==0]; heapq.heapify(ready)
    out=[]
    while ready:
        _,n=heapq.heappop(ready); out.append(n)
        for m in sorted(outgoing[n]):
            incoming[m]-=1
            if incoming[m]==0: heapq.heappush(ready,(-priority.get(m,0.0),m))
    if len(out)!=len(nodes): raise ValueError("cycle prevents teaching order")
    return out
