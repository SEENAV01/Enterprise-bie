"""RE-TEMP-027 — Represent approximate temporal language as bounded intervals."""
from dataclasses import dataclass

@dataclass(frozen=True)
class FuzzyTime:
    center:float
    tolerance:float
    qualifier:str="approximately"

def bounds(t:FuzzyTime):
    if t.tolerance < 0: raise ValueError("tolerance must be non-negative")
    return (t.center-t.tolerance,t.center+t.tolerance)

def fuzzy_relation(a:FuzzyTime,b:FuzzyTime)->str:
    al,ah=bounds(a); bl,bh=bounds(b)
    if ah < bl: return "DEFINITELY_BEFORE"
    if al > bh: return "DEFINITELY_AFTER"
    return "OVERLAP_OR_UNCERTAIN"
