"""RE-TEMP-021 — Resolve whether a temporal assertion applies inside a declared scope."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TemporalScope:
    start: float
    end: float
    inclusive: bool = True

def in_temporal_scope(time: float, scope: TemporalScope) -> bool:
    if scope.start > scope.end:
        raise ValueError("scope start must not exceed end")
    return scope.start <= time <= scope.end if scope.inclusive else scope.start < time < scope.end

def filter_temporal_scope(times, scope: TemporalScope):
    return tuple(t for t in times if in_temporal_scope(t, scope))
