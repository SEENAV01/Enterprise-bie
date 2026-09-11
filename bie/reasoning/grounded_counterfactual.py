from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class CounterfactualIntervention:
    variable: str
    factual_value: str
    intervention_value: str
    assumptions: tuple[str,...] = ()
    evidence_ids: tuple[str,...] = ()

@dataclass(frozen=True)
class CounterfactualResult:
    status: str
    conclusion: str | None
    confidence: float
    assumptions: tuple[str,...]
    evidence_ids: tuple[str,...]
    requires_review: bool
    contradicting_evidence_ids: tuple[str,...] = ()

def evaluate_counterfactual(
    intervention: CounterfactualIntervention,
    *,
    causal_path_supported: bool,
    causal_confidence: float,
    predicted_effect: str | None,
    contradicting_evidence_ids: Iterable[str] = (),
    abstain_below: float = .65,
) -> CounterfactualResult:
    if not intervention.variable.strip():
        raise ValueError("variable required")
    if intervention.factual_value == intervention.intervention_value:
        raise ValueError("intervention must change value")
    if not 0 <= causal_confidence <= 1 or not 0 <= abstain_below <= 1:
        raise ValueError("confidence threshold")
    contradictions=tuple(sorted(set(contradicting_evidence_ids)))
    ev=tuple(sorted(set(intervention.evidence_ids) | set(contradictions)))
    if not causal_path_supported:
        return CounterfactualResult("ABSTAINED",None,causal_confidence,intervention.assumptions,ev,True,contradictions)
    if not predicted_effect:
        return CounterfactualResult("ABSTAINED",None,causal_confidence,intervention.assumptions,ev,True,contradictions)
    if contradictions or causal_confidence < abstain_below:
        return CounterfactualResult("AMBIGUOUS",predicted_effect,causal_confidence,intervention.assumptions,ev,True,contradictions)
    review=bool(intervention.assumptions)
    return CounterfactualResult("RESOLVED",predicted_effect,causal_confidence,intervention.assumptions,ev,review)
