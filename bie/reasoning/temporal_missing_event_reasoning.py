"""RE-TEMP-022 — Detect temporal gaps without inventing missing events."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalGap:
    left: float
    right: float
    duration: float
    status: str = "UNEXPLAINED_GAP"

def detect_temporal_gaps(times, *, threshold: float):
    if threshold < 0: raise ValueError("threshold must be non-negative")
    ordered=sorted(set(times))
    return tuple(TemporalGap(a,b,b-a) for a,b in zip(ordered,ordered[1:]) if b-a > threshold)
