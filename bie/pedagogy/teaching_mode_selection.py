from __future__ import annotations
from dataclasses import dataclass

MODES=("EXPLANATION","INQUIRY","DERIVATION","SIMULATION")

@dataclass(frozen=True)
class TeachingModeDecision:
    mode: str
    reason: str
    confidence: float
    requires_review: bool

def select_teaching_mode(
    *,
    objective_level: str,
    prerequisite_readiness: float,
    mathematical_density: float,
    dynamic_system: bool,
    source_supports_derivation: bool,
) -> TeachingModeDecision:
    if objective_level not in {"REMEMBER","UNDERSTAND","APPLY","ANALYZE","EVALUATE","CREATE"}:
        raise ValueError("objective_level")
    if not 0 <= prerequisite_readiness <= 1 or not 0 <= mathematical_density <= 1:
        raise ValueError("scores")
    if prerequisite_readiness < .5:
        return TeachingModeDecision("EXPLANATION","low prerequisite readiness",.85,False)
    if dynamic_system and objective_level in {"APPLY","ANALYZE","EVALUATE","CREATE"}:
        return TeachingModeDecision("SIMULATION","dynamic behavior benefits from manipulable representation",.9,False)
    if source_supports_derivation and mathematical_density >= .6:
        return TeachingModeDecision("DERIVATION","source and mathematical structure support explicit derivation",.9,False)
    if objective_level in {"ANALYZE","EVALUATE","CREATE"}:
        return TeachingModeDecision("INQUIRY","higher-order objective benefits from guided discovery",.8,False)
    return TeachingModeDecision("EXPLANATION","direct explanation best fits current objective",.8,False)
