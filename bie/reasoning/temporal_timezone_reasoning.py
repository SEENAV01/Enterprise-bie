"""RE-TEMP-026 — Compare timezone-aware instants using explicit offsets."""
from dataclasses import dataclass

@dataclass(frozen=True)
class OffsetInstant:
    local_minutes:int
    utc_offset_minutes:int

def utc_minutes(i:OffsetInstant)->int:
    if not -14*60 <= i.utc_offset_minutes <= 14*60:
        raise ValueError("UTC offset outside supported range")
    return i.local_minutes-i.utc_offset_minutes

def compare_instants(a:OffsetInstant,b:OffsetInstant)->str:
    x,y=utc_minutes(a),utc_minutes(b)
    return "BEFORE" if x<y else "AFTER" if x>y else "SIMULTANEOUS"
