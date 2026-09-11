from dataclasses import dataclass

@dataclass(frozen=True)
class UncertainTime:
    earliest: float
    latest: float
    axis: str = "generic"

@dataclass(frozen=True)
class OffsetBound:
    minimum: float
    maximum: float

def validate_time(t):
    if t.earliest > t.latest:
        raise ValueError("earliest exceeds latest")

def apply_offset(t, offset):
    validate_time(t)
    if offset.minimum > offset.maximum:
        raise ValueError("offset minimum exceeds maximum")
    return UncertainTime(t.earliest + offset.minimum, t.latest + offset.maximum, t.axis)

def propagate_offset_chain(t, offsets):
    out = t
    for off in tuple(offsets):
        out = apply_offset(out, off)
    return out
