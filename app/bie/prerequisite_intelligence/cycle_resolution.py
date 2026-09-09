from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class WeightedEdge:
    source: str
    target: str
    confidence: float

def find_cycle(nodes:set[str], edges:list[WeightedEdge]) -> list[WeightedEdge]:
    adj={n:[] for n in nodes}
    for e in edges: adj[e.source].append(e)
    state={n:0 for n in nodes}; stack=[]; edge_stack=[]
    def dfs(n):
        state[n]=1; stack.append(n)
        for e in adj.get(n,[]):
            if state[e.target]==0:
                edge_stack.append(e)
                found=dfs(e.target)
                if found: return found
                edge_stack.pop()
            elif state[e.target]==1:
                idx=stack.index(e.target)
                return edge_stack[idx:]+[e]
        stack.pop(); state[n]=2
        return []
    for n in sorted(nodes):
        if state[n]==0:
            f=dfs(n)
            if f: return f
    return []

def resolve_cycles(nodes:set[str], edges:list[WeightedEdge]) -> tuple[list[WeightedEdge],list[WeightedEdge]]:
    kept=list(edges); removed=[]
    while True:
        cyc=find_cycle(nodes,kept)
        if not cyc: break
        loser=min(cyc,key=lambda e:(e.confidence,e.source,e.target))
        kept.remove(loser); removed.append(loser)
    return kept,removed
