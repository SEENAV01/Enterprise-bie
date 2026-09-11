from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from bie.reasoning.reasoning_status_semantics import aggregate_status, REVIEW_CONFIDENCE_THRESHOLD

@dataclass(frozen=True)
class FamilyConstraint:
    family: str
    proposition: str
    polarity: str
    status: str
    evidence_ids: tuple[str,...]
    confidence: float

@dataclass(frozen=True)
class ArbitrationResult:
    proposition: str
    status: str
    supporting_families: tuple[str,...]
    opposing_families: tuple[str,...]
    evidence_ids: tuple[str,...]
    confidence: float
    requires_review: bool

def arbitrate_constraints(constraints:Iterable[FamilyConstraint]) -> ArbitrationResult:
    cs=tuple(constraints)
    if not cs: raise ValueError("constraints required")
    props={c.proposition for c in cs}
    if len(props)!=1: raise ValueError("single proposition required")
    for c in cs:
        if c.polarity not in {"SUPPORTS","OPPOSES","UNKNOWN"}: raise ValueError("polarity")
        if not c.family.strip() or not c.evidence_ids or not 0<=c.confidence<=1: raise ValueError("invalid constraint")
    support=tuple(sorted({c.family for c in cs if c.polarity=="SUPPORTS"}))
    oppose=tuple(sorted({c.family for c in cs if c.polarity=="OPPOSES"}))
    ev=tuple(sorted({e for c in cs for e in c.evidence_ids}))
    status=aggregate_status(*(c.status for c in cs)).status
    if support and oppose: status="CONFLICT"
    elif any(c.polarity=="UNKNOWN" for c in cs) and status=="RESOLVED": status="AMBIGUOUS"
    conf=min(c.confidence for c in cs)
    return ArbitrationResult(next(iter(props)),status,support,oppose,ev,conf,
                             status!="RESOLVED" or conf < REVIEW_CONFIDENCE_THRESHOLD)
