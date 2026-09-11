from __future__ import annotations
from dataclasses import asdict
from bie.reasoning.chronology_reasoning import TimeSpan
from bie.reasoning.grounded_result import inference
TASK_ID="BIE-RE-TEMP-014"
def intersect_windows(windows, refs):
    windows=tuple(windows)
    if not windows: raise ValueError("At least one temporal window required")
    axes={w.axis for w in windows}
    if len(axes)!=1: raise ValueError("Incompatible time axes")
    lows=[w.earliest for w in windows if w.earliest is not None]; highs=[w.latest for w in windows if w.latest is not None]
    lo=max(lows) if lows else None; hi=min(highs) if highs else None
    conflict=lo is not None and hi is not None and lo>hi
    value={"axis":windows[0].axis,"intersection":None if conflict else asdict(TimeSpan(lo,hi,windows[0].axis)),"conflicting":conflict,"window_count":len(windows)}
    return inference(TASK_ID,"temporal.window_intersection",{"windows":[asdict(w) for w in windows]},value,refs,status="CONFLICT" if conflict else ("AMBIGUOUS" if lo is None or hi is None or lo!=hi else "RESOLVED"),uncertainty=("Open or non-point intersection remains temporally uncertain",) if not conflict and (lo is None or hi is None or lo!=hi) else ())
