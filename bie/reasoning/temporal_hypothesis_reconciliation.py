"""Temporal hypothesis reconciliation for BIE.

RE-TEMP-019: preserve competing temporal hypotheses instead of forcing
premature certainty when evidence supports multiple timelines.
"""
from dataclasses import dataclass
from typing import Iterable, Tuple

@dataclass(frozen=True)
class TemporalHypothesis:
    hypothesis_id: str
    relation: str
    confidence: float
    evidence_ids: Tuple[str, ...]

@dataclass(frozen=True)
class ReconciliationResult:
    hypotheses: Tuple[TemporalHypothesis, ...]
    status: str
    preferred_id: str | None
    requires_review: bool

def reconcile_temporal_hypotheses(
    hypotheses: Iterable[TemporalHypothesis],
    *,
    preference_margin: float = 0.15,
) -> ReconciliationResult:
    """Rank temporal hypotheses while preserving material alternatives.

    A preferred hypothesis is emitted only when the best supported candidate
    exceeds the runner-up by ``preference_margin``. Otherwise ambiguity is
    explicitly preserved for downstream reasoning/review.
    """
    items = tuple(hypotheses)
    if not items:
        return ReconciliationResult((), "INSUFFICIENT_EVIDENCE", None, True)
    if preference_margin < 0:
        raise ValueError("preference_margin must be non-negative")
    for h in items:
        if not h.hypothesis_id or not h.relation:
            raise ValueError("hypothesis_id and relation are required")
        if not 0.0 <= h.confidence <= 1.0:
            raise ValueError("confidence must be within [0, 1]")

    ranked = tuple(sorted(items, key=lambda h: (-h.confidence, h.hypothesis_id)))
    if len(ranked) == 1:
        only = ranked[0]
        return ReconciliationResult(ranked, "RESOLVED", only.hypothesis_id, False)

    best, second = ranked[0], ranked[1]
    if best.confidence - second.confidence >= preference_margin:
        return ReconciliationResult(ranked, "RESOLVED", best.hypothesis_id, False)

    return ReconciliationResult(ranked, "AMBIGUOUS", None, True)
