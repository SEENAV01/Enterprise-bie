from __future__ import annotations
from typing import Mapping, Iterable

def _reachable(adj: Mapping[str,set[str]], start: str, target: str, skip: tuple[str,str]|None=None) -> bool:
    stack=[start]; seen=set()
    while stack:
        n=stack.pop()
        if n in seen: continue
        seen.add(n)
        for nxt in adj.get(n,set()):
            if skip == (n,nxt): continue
            if nxt == target: return True
            stack.append(nxt)
    return False

def transitive_reduction(nodes: Iterable[str], edges: Iterable[tuple[str,str]]) -> list[tuple[str,str]]:
    ns=set(nodes)
    adj={n:set() for n in ns}
    normalized=set()
    for a,b in edges:
        if a==b: raise ValueError("self-loop not allowed")
        if a not in ns or b not in ns: raise ValueError("unknown node")
        adj[a].add(b); normalized.add((a,b))
    reduced=[]
    for e in sorted(normalized):
        if not _reachable(adj,e[0],e[1],skip=e):
            reduced.append(e)
    return reduced
