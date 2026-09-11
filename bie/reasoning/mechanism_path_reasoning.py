from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Iterable

@dataclass(frozen=True)
class MechanismStep:
    source: str
    target: str
    mechanism: str
    evidence_ids: tuple[str,...]
    confidence: float = 1.0

    def validate(self):
        if not self.source.strip() or not self.target.strip() or not self.mechanism.strip():
            raise ValueError("source/target/mechanism required")
        if self.source == self.target:
            raise ValueError("self step not allowed")
        if not self.evidence_ids:
            raise ValueError("mechanism step requires evidence")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence")

@dataclass(frozen=True)
class MechanismPath:
    nodes: tuple[str,...]
    steps: tuple[MechanismStep,...]
    confidence: float
    evidence_ids: tuple[str,...]

def find_mechanism_paths(
    nodes: Iterable[str],
    steps: Iterable[MechanismStep],
    source: str,
    target: str,
    *,
    max_depth: int = 8
) -> tuple[MechanismPath,...]:
    nodes=tuple(nodes); steps=tuple(steps)
    known=set(nodes)
    if source not in known or target not in known:
        raise ValueError("unknown endpoint")
    if max_depth < 1:
        raise ValueError("max_depth")
    adj={n:[] for n in nodes}
    for s in steps:
        s.validate()
        if s.source not in known or s.target not in known:
            raise ValueError("unknown mechanism node")
        adj[s.source].append(s)
    for n in adj:
        adj[n].sort(key=lambda s:(s.target,s.mechanism,s.evidence_ids))
    q=deque([(source,(source,),())]); out=[]
    while q:
        cur,npath,spath=q.popleft()
        if len(spath) >= max_depth:
            continue
        for s in adj[cur]:
            if s.target in npath:
                continue
            nn=npath+(s.target,); ns=spath+(s,)
            if s.target == target:
                ev=tuple(sorted({e for st in ns for e in st.evidence_ids}))
                out.append(MechanismPath(nn,ns,min(x.confidence for x in ns),ev))
            else:
                q.append((s.target,nn,ns))
    out.sort(key=lambda p:(len(p.steps),p.nodes,tuple(x.mechanism for x in p.steps)))
    return tuple(out)
