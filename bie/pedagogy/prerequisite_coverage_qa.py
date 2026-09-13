from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Iterable

@dataclass(frozen=True)
class PrerequisiteCoverageReport:
    missing_prerequisites: tuple[str,...]
    unbridged_prerequisites: tuple[str,...]
    passed: bool

def prerequisite_coverage_qa(
    required_prerequisites: Iterable[str],
    available_mastery: Mapping[str,float],
    bridged_concepts: Iterable[str],
    *,
    mastery_threshold: float=.7,
) -> PrerequisiteCoverageReport:
    if not 0<=mastery_threshold<=1:
        raise ValueError("threshold")
    required=set(required_prerequisites); bridged=set(bridged_concepts)
    missing=[]; unbridged=[]
    for p in sorted(required):
        m=available_mastery.get(p)
        if m is None:
            missing.append(p)
        elif not 0<=m<=1:
            raise ValueError("mastery")
        elif m<mastery_threshold and p not in bridged:
            unbridged.append(p)
    return PrerequisiteCoverageReport(tuple(missing),tuple(unbridged),not missing and not unbridged)
