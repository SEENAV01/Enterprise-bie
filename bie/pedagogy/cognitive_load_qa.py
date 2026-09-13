from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class CognitiveLoadQAReport:
    overload_segments: tuple[str,...]
    abrupt_jumps: tuple[str,...]
    passed: bool

def cognitive_load_qa(segment_loads, *, max_load:float=1.8, max_jump:float=.7) -> CognitiveLoadQAReport:
    if not math.isfinite(max_load) or not math.isfinite(max_jump) or max_load<=0 or max_jump<0:
        raise ValueError("thresholds")
    items=tuple(segment_loads)
    overload=[]; jumps=[]
    prev=None
    for sid,load in items:
        if not sid.strip() or not math.isfinite(load) or load<0:
            raise ValueError("segment")
        if load>max_load:
            overload.append(sid)
        if prev is not None and abs(load-prev[1])>max_jump:
            jumps.append(prev[0]+"->"+sid)
        prev=(sid,load)
    return CognitiveLoadQAReport(tuple(overload),tuple(jumps),not overload and not jumps)
