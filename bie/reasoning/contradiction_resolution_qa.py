from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from bie.reasoning.decision_contracts import ReasoningDecision

@dataclass(frozen=True)
class ContradictionResolution:
    contradiction_id: str
    evidence_ids: tuple[str, ...]
    disposition: str
    rationale: str
    resolved_by_decision_id: str | None = None

@dataclass(frozen=True)
class ContradictionQAReport:
    decision_id: str
    unresolved_contradiction_ids: tuple[str, ...]
    invalid_contradiction_ids: tuple[str, ...]
    passed: bool
    requires_review: bool

_ALLOWED={"RESOLVED","PRESERVED_AMBIGUITY","ESCALATED"}

def evaluate_contradiction_resolution(
    decision: ReasoningDecision,
    resolutions: Iterable[ContradictionResolution],
) -> ContradictionQAReport:
    if not isinstance(decision,ReasoningDecision): raise TypeError("decision must be ReasoningDecision")
    decision.validate()
    resolutions=tuple(resolutions)
    ids=[r.contradiction_id for r in resolutions]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate contradiction_id")
    evidence={r.artifact_id for r in decision.evidence_refs}
    invalid=[]; unresolved=[]
    for r in resolutions:
        if not r.contradiction_id.strip() or not r.rationale.strip() or r.disposition not in _ALLOWED:
            invalid.append(r.contradiction_id or "<blank>"); continue
        if len(r.evidence_ids)<2 or any(e not in evidence for e in r.evidence_ids):
            invalid.append(r.contradiction_id); continue
        if r.disposition != "RESOLVED":
            unresolved.append(r.contradiction_id)
        elif r.resolved_by_decision_id not in {None,decision.decision_id}:
            invalid.append(r.contradiction_id)
    contradicting={r.artifact_id for r in decision.evidence_refs if r.role=="contradicting"}
    covered={e for r in resolutions for e in r.evidence_ids}
    if contradicting - covered:
        unresolved.extend("uncovered:"+e for e in sorted(contradicting-covered))
    unresolved=tuple(sorted(set(unresolved))); invalid=tuple(sorted(set(invalid)))
    passed=not invalid and not unresolved
    return ContradictionQAReport(decision.decision_id,unresolved,invalid,passed,
        (not passed) or decision.requires_review)
