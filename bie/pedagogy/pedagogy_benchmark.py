from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True)
class PedagogyBenchmarkReport:
    metrics: tuple[tuple[str,float],...]
    failed_metrics: tuple[str,...]
    score: float
    passed: bool

def benchmark_pedagogy(
    metrics: Mapping[str,float],
    thresholds: Mapping[str,float],
    *,
    critical_metrics=("objective_coverage","prerequisite_coverage","assessment_alignment"),
) -> PedagogyBenchmarkReport:
    if not thresholds:
        raise ValueError("thresholds")
    failed=[]
    normalized=[]
    for name,threshold in sorted(thresholds.items()):
        if not 0<=threshold<=1:
            raise ValueError("threshold")
        value=metrics.get(name)
        if value is None or not 0<=value<=1:
            failed.append(name)
            normalized.append((name,0.0 if value is None else value))
        else:
            normalized.append((name,value))
            if value<threshold:
                failed.append(name)
    score=sum(v for _,v in normalized)/len(normalized)
    critical_failure=any(x in set(critical_metrics) for x in failed)
    return PedagogyBenchmarkReport(tuple(normalized),tuple(sorted(set(failed))),score,not failed and not critical_failure)
