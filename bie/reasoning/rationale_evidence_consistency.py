from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from bie.reasoning.decision_contracts import ReasoningDecision, EvidenceRef

@dataclass(frozen=True)
class RationaleEvidenceFinding:
    code: str
    severity: str
    message: str
    evidence_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class RationaleEvidenceReport:
    decision_id: str
    passed: bool
    findings: tuple[RationaleEvidenceFinding, ...]
    cited_evidence_ids: tuple[str, ...]
    contradicting_evidence_ids: tuple[str, ...]
    requires_review: bool

def evaluate_rationale_evidence_consistency(
    decision: ReasoningDecision,
    *,
    rationale_evidence_ids: Iterable[str] | None = None,
) -> RationaleEvidenceReport:
    if not isinstance(decision, ReasoningDecision):
        raise TypeError("decision must be ReasoningDecision")
    decision.validate()
    refs = tuple(decision.evidence_refs)
    by_id = {r.artifact_id: r for r in refs}
    cited = tuple(sorted(set(rationale_evidence_ids or by_id.keys())))
    unknown = tuple(x for x in cited if x not in by_id)
    findings = []
    if unknown:
        findings.append(RationaleEvidenceFinding(
            "UNKNOWN_RATIONALE_EVIDENCE", "ERROR",
            "Rationale cites evidence not bound to the decision.", unknown))
    if not decision.rationale_summary.strip():
        findings.append(RationaleEvidenceFinding(
            "EMPTY_RATIONALE", "ERROR", "Decision rationale is empty."))
    contradiction_ids = tuple(sorted(r.artifact_id for r in refs if r.role == "contradicting"))
    if contradiction_ids and not decision.requires_review:
        findings.append(RationaleEvidenceFinding(
            "UNREVIEWED_CONTRADICTION", "ERROR",
            "Contradicting evidence exists but decision is not marked for review.",
            contradiction_ids))
    primary_support = tuple(r for r in refs if r.role in {"primary","supporting","derived","constraint"})
    if not primary_support:
        findings.append(RationaleEvidenceFinding(
            "NO_SUPPORTING_EVIDENCE", "ERROR",
            "No supporting/primary/derived/constraint evidence is bound to the rationale."))
    if decision.confidence > min(r.strength for r in refs) + 1e-12:
        findings.append(RationaleEvidenceFinding(
            "CONFIDENCE_EXCEEDS_WEAKEST_EVIDENCE", "WARNING",
            "Decision confidence exceeds the weakest bound evidence strength."))
    passed = not any(f.severity == "ERROR" for f in findings)
    return RationaleEvidenceReport(
        decision.decision_id, passed, tuple(findings), cited,
        contradiction_ids, (not passed) or bool(contradiction_ids) or decision.requires_review)
