from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalCausalAssessment:
    temporal_relation: str
    causal_claim_allowed: bool
    reason_code: str
    requires_review: bool

_ALLOWED_REL={"BEFORE","AFTER","SIMULTANEOUS","OVERLAPS","UNKNOWN","CONFLICT"}

def assess_temporal_causal_claim(
    temporal_relation: str,
    *,
    causal_evidence_ids: tuple[str,...] = (),
    mechanism_supported: bool = False,
    contradicting_evidence_ids: tuple[str,...] = (),
) -> TemporalCausalAssessment:
    if temporal_relation not in _ALLOWED_REL:
        raise ValueError("unsupported temporal relation")
    if temporal_relation != "BEFORE":
        return TemporalCausalAssessment(
            temporal_relation, False, "TEMPORAL_PRECEDENCE_NOT_ESTABLISHED", True
        )
    if not causal_evidence_ids:
        return TemporalCausalAssessment(
            temporal_relation, False, "BEFORE_DOES_NOT_IMPLY_CAUSES", True
        )
    if not mechanism_supported:
        return TemporalCausalAssessment(
            temporal_relation, False, "MECHANISM_NOT_SUPPORTED", True
        )
    if contradicting_evidence_ids:
        return TemporalCausalAssessment(
            temporal_relation, False, "CONTRADICTING_CAUSAL_EVIDENCE", True
        )
    return TemporalCausalAssessment(
        temporal_relation, True, "SUPPORTED_CAUSAL_CLAIM", False
    )
