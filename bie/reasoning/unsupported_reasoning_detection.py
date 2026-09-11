from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping
from bie.reasoning.decision_contracts import ReasoningDecision

@dataclass(frozen=True)
class ReasoningClaim:
    claim_id: str
    text: str
    evidence_ids: tuple[str, ...] = ()
    derived_from_claim_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class UnsupportedReasoningReport:
    decision_id: str
    unsupported_claim_ids: tuple[str, ...]
    unresolved_evidence_ids: tuple[str, ...]
    cyclic_claim_ids: tuple[str, ...]
    passed: bool
    requires_review: bool

def detect_unsupported_reasoning(
    decision: ReasoningDecision,
    claims: Iterable[ReasoningClaim],
) -> UnsupportedReasoningReport:
    if not isinstance(decision, ReasoningDecision):
        raise TypeError("decision must be ReasoningDecision")
    decision.validate()
    claims=tuple(claims)
    ids=[c.claim_id for c in claims]
    if any(not isinstance(c,ReasoningClaim) or not c.claim_id.strip() or not c.text.strip() for c in claims):
        raise ValueError("claims require nonblank id and text")
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate claim_id")
    by_id={c.claim_id:c for c in claims}
    known_evidence={e.artifact_id for e in decision.evidence_refs}
    unresolved=set()
    unsupported=set()

    for c in claims:
        for eid in c.evidence_ids:
            if eid not in known_evidence: unresolved.add(eid)
        for parent in c.derived_from_claim_ids:
            if parent not in by_id: unsupported.add(c.claim_id)
        if not c.evidence_ids and not c.derived_from_claim_ids:
            unsupported.add(c.claim_id)

    visiting=set(); visited=set(); cyclic=set()
    def dfs(cid, trail):
        if cid in visiting:
            i=trail.index(cid) if cid in trail else 0
            cyclic.update(trail[i:]); return
        if cid in visited: return
        visiting.add(cid)
        for p in by_id[cid].derived_from_claim_ids:
            if p in by_id: dfs(p, trail+[p])
        visiting.remove(cid); visited.add(cid)
    for cid in ids: dfs(cid,[cid])
    unsupported.update(cyclic)
    for c in claims:
        if any(e not in known_evidence for e in c.evidence_ids):
            unsupported.add(c.claim_id)

    passed=not unsupported and not unresolved
    return UnsupportedReasoningReport(
        decision.decision_id, tuple(sorted(unsupported)),
        tuple(sorted(unresolved)), tuple(sorted(cyclic)),
        passed, not passed or decision.requires_review)
