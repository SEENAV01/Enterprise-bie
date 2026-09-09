from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
@dataclass(frozen=True)
class Evidence:
    source_id: str
    kind: str
    weight: float
    excerpt: str = ""
    def __post_init__(self):
        if not self.source_id: raise ValueError("source_id required")
        if not 0 <= self.weight <= 1: raise ValueError("weight must be in [0,1]")
@dataclass(frozen=True)
class EvidenceSummary:
    confidence: float
    source_count: int
    kinds: tuple[str,...]
def aggregate_evidence(items: Iterable[Evidence]) -> EvidenceSummary:
    unique={}
    for e in items: unique[(e.source_id,e.kind,e.excerpt)]=e
    vals=list(unique.values())
    # noisy-OR: independent corroborating evidence increases confidence without exceeding 1
    p_not=1.0
    for e in vals: p_not*=1-e.weight
    return EvidenceSummary(round(1-p_not,6),len({e.source_id for e in vals}),tuple(sorted({e.kind for e in vals})))
