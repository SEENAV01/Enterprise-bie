from __future__ import annotations
from dataclasses import dataclass
from bie.reasoning.decision_contracts import ReasoningDecision

@dataclass(frozen=True)
class ConfidenceFinding:
    code: str
    severity: str
    message: str

@dataclass(frozen=True)
class ConfidenceQAReport:
    decision_id: str
    findings: tuple[ConfidenceFinding, ...]
    conservative_ceiling: float
    passed: bool
    requires_review: bool

def evaluate_confidence(
    decision: ReasoningDecision,
    *,
    review_threshold: float = .75,
    tolerance: float = 1e-9,
) -> ConfidenceQAReport:
    if not isinstance(decision,ReasoningDecision):
        raise TypeError("decision must be ReasoningDecision")
    if not (0 <= review_threshold <= 1): raise ValueError("review_threshold must be in [0,1]")
    if tolerance < 0: raise ValueError("tolerance must be nonnegative")
    decision.validate()
    refs=tuple(decision.evidence_refs)
    ceiling=min(r.strength for r in refs)
    findings=[]
    if decision.confidence > ceiling + tolerance:
        findings.append(ConfidenceFinding(
            "OVERCONFIDENT_VS_EVIDENCE","ERROR",
            "Decision confidence exceeds conservative weakest-evidence ceiling."))
    if decision.confidence < review_threshold and not decision.requires_review:
        findings.append(ConfidenceFinding(
            "LOW_CONFIDENCE_WITHOUT_REVIEW","ERROR",
            "Decision below review threshold is not marked for review."))
    if any(r.role=="contradicting" for r in refs) and not decision.requires_review:
        findings.append(ConfidenceFinding(
            "CONFLICT_WITHOUT_REVIEW","ERROR",
            "Contradicting evidence requires review regardless of scalar confidence."))
    if decision.uncertainty and not decision.requires_review:
        findings.append(ConfidenceFinding(
            "UNCERTAINTY_WITHOUT_REVIEW","ERROR",
            "Explicit uncertainty exists but review is disabled."))
    passed=not any(f.severity=="ERROR" for f in findings)
    return ConfidenceQAReport(decision.decision_id,tuple(findings),ceiling,passed,
                              (not passed) or decision.requires_review)
