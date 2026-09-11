"""RE-TEMP-024 — Central policy for evidence-aware temporal abstention."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalDecisionContext:
    confidence: float
    evidence_count: int
    contradiction_count: int = 0

@dataclass(frozen=True)
class TemporalDecision:
    may_assert: bool
    status: str

def temporal_decision(ctx: TemporalDecisionContext, *, min_confidence=.65, min_evidence=1):
    if not 0 <= ctx.confidence <= 1: raise ValueError("confidence must be within [0,1]")
    if ctx.evidence_count < 0 or ctx.contradiction_count < 0: raise ValueError("counts must be non-negative")
    if ctx.contradiction_count: return TemporalDecision(False,"ABSTAIN_CONTRADICTION")
    if ctx.evidence_count < min_evidence: return TemporalDecision(False,"ABSTAIN_INSUFFICIENT_EVIDENCE")
    if ctx.confidence < min_confidence: return TemporalDecision(False,"ABSTAIN_LOW_CONFIDENCE")
    return TemporalDecision(True,"ASSERT")
