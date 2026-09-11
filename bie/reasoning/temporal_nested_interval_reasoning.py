"""RE-TEMP-036 — Reason over nested intervals with explicit containment semantics."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Interval:
    start:float
    end:float
def validate(i):
    if i.start>i.end: raise ValueError("interval start exceeds end")
def interval_relation(a:Interval,b:Interval):
    validate(a); validate(b)
    if a.start==b.start and a.end==b.end:return "EQUAL"
    if b.start<=a.start and a.end<=b.end:return "A_WITHIN_B"
    if a.start<=b.start and b.end<=a.end:return "B_WITHIN_A"
    if a.end<b.start or b.end<a.start:return "DISJOINT"
    return "OVERLAP"
