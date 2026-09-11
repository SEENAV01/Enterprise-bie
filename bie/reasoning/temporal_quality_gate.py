"""RE-TEMP-034 — Explicit pre-release quality gate for temporal reasoning outputs."""
from dataclasses import dataclass
@dataclass(frozen=True)
class TemporalQualitySignals:
    grounded:bool
    consistent:bool
    confidence:float
    provenance_complete:bool
    unsupported_inference_count:int=0
@dataclass(frozen=True)
class TemporalQualityDecision:
    passed:bool
    blockers:tuple[str,...]
def evaluate_temporal_quality(s:TemporalQualitySignals, *, min_confidence=.65):
    if not 0<=s.confidence<=1: raise ValueError("confidence must be within [0,1]")
    if s.unsupported_inference_count<0: raise ValueError("unsupported count must be non-negative")
    b=[]
    if not s.grounded:b.append("ungrounded")
    if not s.consistent:b.append("inconsistent")
    if s.confidence<min_confidence:b.append("low_confidence")
    if not s.provenance_complete:b.append("incomplete_provenance")
    if s.unsupported_inference_count:b.append("unsupported_inference")
    return TemporalQualityDecision(not b,tuple(b))
