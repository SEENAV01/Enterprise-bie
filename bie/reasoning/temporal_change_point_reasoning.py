"""RE-TEMP-032 — Detect material value transitions in ordered observations."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Observation:
    time: float
    value: float
@dataclass(frozen=True)
class ChangePoint:
    time: float
    delta: float
def detect_change_points(observations, *, min_delta:float):
    if min_delta < 0: raise ValueError("min_delta must be non-negative")
    xs=sorted(observations,key=lambda x:x.time)
    if len({x.time for x in xs}) != len(xs): raise ValueError("duplicate observation time")
    return tuple(ChangePoint(b.time,b.value-a.value) for a,b in zip(xs,xs[1:]) if abs(b.value-a.value)>=min_delta)
