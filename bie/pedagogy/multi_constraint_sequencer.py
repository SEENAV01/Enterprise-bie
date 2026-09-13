from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import heapq
import math

@dataclass(frozen=True)
class CurriculumNode:
    node_id: str
    source_order: int
    cognitive_load: float
    objective_priority: float
    remediation_required: bool=False

@dataclass(frozen=True)
class SequenceConstraint:
    before: str
    after: str
    kind: str
    hard: bool=True
    strength: float=1.0

@dataclass(frozen=True)
class SequencingResult:
    order: tuple[str,...]
    violated_soft_constraints: tuple[tuple[str,str,str],...]
    total_load: float

def sequence_curriculum(
    nodes: Iterable[CurriculumNode],
    constraints: Iterable[SequenceConstraint],
    *,
    max_adjacent_load: float=1.8,
) -> SequencingResult:
    if not math.isfinite(max_adjacent_load) or max_adjacent_load<=0:
        raise ValueError("finite positive adjacent-load budget required")
    ns=tuple(nodes); cs=tuple(constraints)
    ids=[n.node_id for n in ns]
    if len(ids)!=len(set(ids)) or not ids:
        raise ValueError("unique nodes required")
    known=set(ids)
    byid={n.node_id:n for n in ns}
    for n in ns:
        if n.source_order<0 or not 0<=n.cognitive_load<=1 or not 0<=n.objective_priority<=1:
            raise ValueError("invalid node")
    hard=[c for c in cs if c.hard]
    soft=[c for c in cs if not c.hard]
    indeg={i:0 for i in ids}; adj={i:[] for i in ids}
    for c in cs:
        if type(c.hard) is not bool: raise ValueError("hard constraint flag must be boolean")
        if c.before not in known or c.after not in known or not 0<=c.strength<=1:
            raise ValueError("invalid constraint")
    for c in hard:
        adj[c.before].append(c.after); indeg[c.after]+=1
    # stable priority: remediation first, objective priority desc, source order, id
    heap=[]
    for i in ids:
        if indeg[i]==0:
            n=byid[i]; heapq.heappush(heap,(0 if n.remediation_required else 1,-n.objective_priority,n.source_order,n.node_id))
    out=[]
    while heap:
        *_, cur=heapq.heappop(heap); out.append(cur)
        for nxt in sorted(adj[cur]):
            indeg[nxt]-=1
            if indeg[nxt]==0:
                n=byid[nxt]; heapq.heappush(heap,(0 if n.remediation_required else 1,-n.objective_priority,n.source_order,n.node_id))
    if len(out)!=len(ids):
        raise ValueError("hard-constraint cycle")
    pos={x:i for i,x in enumerate(out)}
    violated=tuple(sorted((c.before,c.after,c.kind) for c in soft if pos[c.before]>=pos[c.after]))
    # adjacent lesson load guard; hard failure because section-level planner should split first.
    for a,b in zip(out,out[1:]):
        if byid[a].cognitive_load + byid[b].cognitive_load > max_adjacent_load:
            raise ValueError("adjacent cognitive-load budget exceeded")
    return SequencingResult(tuple(out),violated,sum(n.cognitive_load for n in ns))
