"""RE-TEMP-040 — Prevent false exactness when temporal precisions differ."""
from dataclasses import dataclass
@dataclass(frozen=True)
class PreciseTime:
    value:float
    precision:str
_RANK={"year":1,"month":2,"day":3,"hour":4,"minute":5,"second":6}
def compatible_precision(a:PreciseTime,b:PreciseTime):
    if a.precision not in _RANK or b.precision not in _RANK: raise ValueError("unsupported precision")
    rank=min(_RANK[a.precision],_RANK[b.precision])
    p=next(k for k,v in _RANK.items() if v==rank)
    return p
def exact_comparison_allowed(a,b): return a.precision==b.precision and compatible_precision(a,b)==a.precision
