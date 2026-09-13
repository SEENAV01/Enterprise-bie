from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Iterable

@dataclass(frozen=True)
class AssessmentAlignmentReport:
    uncovered_objectives: tuple[str,...]
    cognitive_mismatches: tuple[str,...]
    passed: bool

_LEVEL={"REMEMBER":1,"UNDERSTAND":2,"APPLY":3,"ANALYZE":4,"EVALUATE":5,"CREATE":6}

def assessment_alignment(
    objective_levels: Mapping[str,str],
    assessment_items: Iterable[tuple[str,str,str]],
) -> AssessmentAlignmentReport:
    # item tuple: (item_id, objective_id, assessed_level)
    covered=set(); mismatch=[]
    for item_id,oid,level in assessment_items:
        if not item_id.strip() or oid not in objective_levels or level not in _LEVEL:
            raise ValueError("invalid assessment item")
        target=objective_levels[oid]
        if target not in _LEVEL:
            raise ValueError("objective level")
        covered.add(oid)
        # assessment may match or exceed target by one level, but not under-assess.
        if _LEVEL[level] < _LEVEL[target]:
            mismatch.append(item_id)
    missing=tuple(sorted(set(objective_levels)-covered))
    mismatch=tuple(sorted(mismatch))
    return AssessmentAlignmentReport(missing,mismatch,not missing and not mismatch)
