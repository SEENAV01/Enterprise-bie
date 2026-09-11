"""RE-TEMP-030 — Relate temporal facts expressed at different scales."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ScaledTime:
    value: float
    unit: str
_FACTORS={"second":1.0,"minute":60.0,"hour":3600.0,"day":86400.0}
def to_seconds(t:ScaledTime)->float:
    u=t.unit.lower()
    if u not in _FACTORS: raise ValueError("unsupported temporal unit")
    return t.value*_FACTORS[u]
def compare_scaled_times(a:ScaledTime,b:ScaledTime)->str:
    x,y=to_seconds(a),to_seconds(b)
    return "SHORTER" if x<y else "LONGER" if x>y else "EQUIVALENT"
