from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Iterable

@dataclass(frozen=True)
class ObjectiveCoverageReport:
    coverage: float
    uncovered_objectives: tuple[str,...]
    weakly_covered_objectives: tuple[str,...]
    passed: bool

def objective_coverage_qa(
    objective_to_activities: Mapping[str, Iterable[str]],
    required_objectives: Iterable[str],
    *,
    minimum_activities: int = 1,
) -> ObjectiveCoverageReport:
    if minimum_activities<1:
        raise ValueError("minimum_activities")
    required=tuple(sorted(set(required_objectives)))
    if not required:
        raise ValueError("required objectives")
    uncovered=[]; weak=[]
    for oid in required:
        acts=tuple(a for a in objective_to_activities.get(oid,()) if str(a).strip())
        if not acts:
            uncovered.append(oid)
        elif len(set(acts))<minimum_activities:
            weak.append(oid)
    covered=len(required)-len(uncovered)-len(weak)
    coverage=covered/len(required)
    return ObjectiveCoverageReport(coverage,tuple(uncovered),tuple(weak),coverage==1.0)
