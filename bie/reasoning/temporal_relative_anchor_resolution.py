"""RE-TEMP-035 — Resolve relative temporal expressions only against explicit anchors."""
from dataclasses import dataclass
@dataclass(frozen=True)
class RelativeTime:
    offset: float
    unit: str
@dataclass(frozen=True)
class AnchoredTime:
    value: float
    unit: str
_FACT={"second":1,"minute":60,"hour":3600,"day":86400}
def resolve_relative_time(relative:RelativeTime, anchor:AnchoredTime|None):
    if anchor is None: raise ValueError("explicit temporal anchor required")
    ru,au=relative.unit.lower(),anchor.unit.lower()
    if ru not in _FACT or au not in _FACT: raise ValueError("unsupported unit")
    seconds=anchor.value*_FACT[au]+relative.offset*_FACT[ru]
    return AnchoredTime(seconds/_FACT[au],au)
