from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Iterable

@dataclass(frozen=True)
class DependencyEdge:
    source: str
    target: str
    evidence_ids: tuple[str,...] = ()
    relation: str = "depends_on"

@dataclass(frozen=True)
class ImpactPath:
    target: str
    nodes: tuple[str,...]
    edges: tuple[DependencyEdge,...]
    evidence_ids: tuple[str,...]

def downstream_impact_paths(nodes: Iterable[str], edges: Iterable[DependencyEdge], start: str) -> tuple[ImpactPath,...]:
    nodes=tuple(nodes); edges=tuple(edges)
    known=set(nodes)
    if len(known)!=len(nodes): raise ValueError("duplicate node")
    if start not in known: raise ValueError("unknown start")
    adj={n:[] for n in nodes}
    for e in edges:
        if e.source not in known or e.target not in known: raise ValueError("unknown node")
        if not e.relation.strip(): raise ValueError("blank relation")
        adj[e.source].append(e)
    for n in adj: adj[n].sort(key=lambda e:(e.target,e.relation,e.evidence_ids))
    q=deque([(start,(start,),())]); best={start:(start,)}
    paths={}
    while q:
        cur,npath,epath=q.popleft()
        for e in adj[cur]:
            if e.target in npath: continue
            nn=npath+(e.target,); ne=epath+(e,)
            old=best.get(e.target)
            if old is None or (len(nn),nn)<(len(old),old):
                best[e.target]=nn
                ev=tuple(sorted({x for xedge in ne for x in xedge.evidence_ids}))
                paths[e.target]=ImpactPath(e.target,nn,ne,ev)
                q.append((e.target,nn,ne))
    return tuple(paths[k] for k in sorted(paths))
