from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class ConfidenceDecision:
    raw: float
    calibrated: float
    band: str
    requires_review: bool
def calibrate_confidence(raw: float, evidence_sources: int=1, contradiction: float=0.0,
                         accept_threshold: float=.75, review_threshold: float=.45) -> ConfidenceDecision:
    if not 0<=raw<=1 or not 0<=contradiction<=1: raise ValueError("scores must be in [0,1]")
    if evidence_sources < 0: raise ValueError("evidence_sources must be non-negative")
    corroboration=min(.12,.03*max(0,evidence_sources-1))
    calibrated=max(0.0,min(1.0,raw+corroboration-.5*contradiction))
    calibrated=round(calibrated,6)
    band="accepted" if calibrated>=accept_threshold else ("review" if calibrated>=review_threshold else "rejected")
    return ConfidenceDecision(raw,calibrated,band,band=="review")
