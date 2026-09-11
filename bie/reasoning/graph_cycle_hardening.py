from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Hashable

@dataclass(frozen=True)
class CycleWitness:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    canonical_key: tuple[str, ...]
    break_candidates: tuple[tuple[str, str], ...]

def _canon_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    body=cycle[:-1]
    rotations=[body[i:]+body[:i] for i in range(len(body))]
    # Rotations preserve directed edges; reversing a cycle can invent edges.
    best=min(rotations)
    return best+(best[0],)

def find_canonical_cycles(nodes: Iterable[str], edges: Iterable[tuple[str,str]]) -> tuple[CycleWitness,...]:
    nodes=tuple(nodes); edges=tuple(edges)
    if len(nodes)!=len(set(nodes)): raise ValueError("duplicate node")
    known=set(nodes); adj={n:[] for n in nodes}
    for a,b in edges:
        if a not in known or b not in known: raise ValueError("unknown node")
        adj[a].append(b)
    for n in adj: adj[n]=sorted(set(adj[n]))
    found={}
    def dfs(start,cur,path):
        for nxt in adj[cur]:
            if nxt==start:
                cyc=_canon_cycle(tuple(path+[start]))
                found[cyc]=cyc
            elif nxt not in path and nxt>=start:
                dfs(start,nxt,path+[nxt])
    for start in sorted(nodes):
        dfs(start,start,[start])
    out=[]
    edge_set=set(edges)
    for cyc in sorted(found):
        es=tuple((cyc[i],cyc[i+1]) for i in range(len(cyc)-1))
        # deterministic least-disruptive proposal surface; caller may score externally
        candidates=tuple(sorted(es))
        out.append(CycleWitness(cyc,es,cyc,candidates))
    return tuple(out)

def propose_cycle_breaks(witnesses: Iterable[CycleWitness]) -> tuple[tuple[str,str],...]:
    witnesses=tuple(witnesses)
    # deterministic greedy edge hitting set; proposal only, never silently mutates graph
    remaining=[set(w.edges) for w in witnesses]
    chosen=[]
    while remaining:
        counts={}
        for es in remaining:
            for e in es: counts[e]=counts.get(e,0)+1
        edge=min(((-c,e) for e,c in counts.items()))[1]
        chosen.append(edge)
        remaining=[es for es in remaining if edge not in es]
    return tuple(chosen)
