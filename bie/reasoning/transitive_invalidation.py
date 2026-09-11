from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Iterable

@dataclass(frozen=True)
class DecisionDependency:
    upstream: str
    downstream: str
    evidence_ids: tuple[str,...] = ()

@dataclass(frozen=True)
class InvalidationRecord:
    decision_id: str
    reason: str
    source_ids: tuple[str,...]
    propagation_path: tuple[str,...]

def propagate_invalidation(
    decision_evidence: dict[str, Iterable[str]],
    dependencies: Iterable[DecisionDependency],
    changed_evidence_ids: Iterable[str],
) -> tuple[InvalidationRecord,...]:
    changed=set(changed_evidence_ids)
    decisions=set(decision_evidence)
    adj={d:[] for d in decisions}
    for dep in dependencies:
        if dep.upstream not in decisions or dep.downstream not in decisions:
            raise ValueError("unknown decision dependency")
        adj[dep.upstream].append(dep.downstream)
    for d in adj: adj[d]=sorted(set(adj[d]))
    records={}
    q=deque()
    for d,ev in sorted(decision_evidence.items()):
        hit=tuple(sorted(changed.intersection(set(ev))))
        if hit:
            records[d]=InvalidationRecord(d,"CHANGED_EVIDENCE",hit,(d,))
            q.append(d)
    while q:
        cur=q.popleft()
        rec=records[cur]
        for nxt in adj[cur]:
            candidate=rec.propagation_path+(nxt,)
            if nxt not in records or (len(candidate),candidate)<(len(records[nxt].propagation_path),records[nxt].propagation_path):
                records[nxt]=InvalidationRecord(nxt,"UPSTREAM_INVALIDATED",(cur,),candidate)
                q.append(nxt)
    return tuple(records[k] for k in sorted(records))
