"""RE-TEMP-020 — Guard temporal counterfactual reasoning against impossible premises."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalCounterfactual:
    premise_time: float
    required_before: float | None = None
    required_after: float | None = None

@dataclass(frozen=True)
class CounterfactualAssessment:
    admissible: bool
    status: str
    reasons: tuple[str, ...]

def assess_temporal_counterfactual(cf: TemporalCounterfactual) -> CounterfactualAssessment:
    reasons=[]
    if cf.required_before is not None and cf.premise_time >= cf.required_before:
        reasons.append("violates_required_before")
    if cf.required_after is not None and cf.premise_time <= cf.required_after:
        reasons.append("violates_required_after")
    if cf.required_before is not None and cf.required_after is not None and cf.required_after >= cf.required_before:
        reasons.append("inconsistent_bounds")
    return CounterfactualAssessment(not reasons, "ADMISSIBLE" if not reasons else "REJECTED", tuple(reasons))
