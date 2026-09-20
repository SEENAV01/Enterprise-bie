from __future__ import annotations
from dataclasses import dataclass
from .visual_qa_contracts import VisualBenchmarkError, score, token, fingerprint

WEIGHTS={"semantic_alignment":.30,"layout_qa":.25,"clutter_qa":.15,"asset_qa":.30}
FLOORS={"semantic_alignment":.90,"layout_qa":.85,"clutter_qa":.75,"asset_qa":.75}

@dataclass(frozen=True)
class VisualBenchmarkReport:
    benchmark_id: str
    weighted_score: float
    passed: bool
    hard_floor_failures: tuple[str,...]
    blockers: tuple[str,...]
    component_scores: dict
    review_required: bool = True
    accepted: bool = False
    fingerprint: str = ""

def evaluate_visual_benchmark(results, benchmark_id="vis-original-benchmark", threshold=.85):
    by={r.dimension:r for r in results}
    if set(by)!=set(WEIGHTS): raise VisualBenchmarkError("benchmark requires semantic/layout/clutter/asset dimensions")
    threshold=score(threshold,"threshold")
    weighted=sum(by[k].score*WEIGHTS[k] for k in WEIGHTS)
    floors=tuple(sorted(k for k in WEIGHTS if by[k].score<FLOORS[k]))
    blockers=tuple(sorted({b for r in by.values() for b in r.blockers}))
    passed=weighted>=threshold and not floors and not blockers
    component={k:by[k].score for k in sorted(by)}
    payload={"benchmark_id":benchmark_id,"weighted":weighted,"floors":floors,"blockers":blockers,"component":component}
    return VisualBenchmarkReport(token(benchmark_id,"benchmark_id"),round(weighted,6),passed,floors,blockers,component,True,False,fingerprint(payload))
