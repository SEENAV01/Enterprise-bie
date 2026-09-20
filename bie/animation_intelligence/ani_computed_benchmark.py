from dataclasses import dataclass

class ComputedBenchmarkError(ValueError): pass

@dataclass(frozen=True)
class BenchmarkArtifact:
    case_id:str
    required_track_ids:tuple[str,...]
    produced_track_ids:tuple[str,...]
    qa_blockers:tuple[str,...]
    trace_blockers:tuple[str,...]
    sceneir_blockers:tuple[str,...]
    sync_error_ms:int
    motion_budget_ratio:float
    empirical_render_status:str="NOT_RUN"

@dataclass(frozen=True)
class ComputedCaseMetrics:
    case_id:str
    coverage:float
    qa_integrity:float
    trace_integrity:float
    sceneir_readiness:float
    sync_score:float
    motion_score:float
    aggregate:float
    empirical_render_status:str
    accepted:bool=False

@dataclass(frozen=True)
class BenchmarkReport:
    status:str
    cases:tuple[ComputedCaseMetrics,...]
    aggregate:float
    blockers:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

def compute_case_metrics(a):
    required=set(a.required_track_ids); produced=set(a.produced_track_ids)
    coverage=1.0 if not required else len(required & produced)/len(required)
    qa=1.0 if not a.qa_blockers else 0.0
    trace=1.0 if not a.trace_blockers else 0.0
    sceneir=1.0 if not a.sceneir_blockers else 0.0
    sync=max(0.0,1.0-min(abs(a.sync_error_ms)/1000.0,1.0))
    motion=max(0.0,1.0-max(a.motion_budget_ratio-1.0,0.0))
    agg=(coverage+qa+trace+sceneir+sync+motion)/6.0
    return ComputedCaseMetrics(a.case_id,round(coverage,6),qa,trace,sceneir,round(sync,6),round(motion,6),
                               round(agg,6),a.empirical_render_status,False)

def run_computed_benchmark(artifacts, *, metric_floor=.80, aggregate_floor=.86, require_empirical_render=False):
    artifacts=tuple(artifacts)
    if not artifacts:raise ComputedBenchmarkError("benchmark artifacts required")
    metrics=tuple(compute_case_metrics(a) for a in artifacts)
    blockers=[]
    for m in metrics:
        vals=(m.coverage,m.qa_integrity,m.trace_integrity,m.sceneir_readiness,m.sync_score,m.motion_score)
        if any(v<metric_floor for v in vals):blockers.append("metric_below_floor:"+m.case_id)
        if require_empirical_render and m.empirical_render_status!="PASS":
            blockers.append("empirical_render_not_passed:"+m.case_id)
    aggregate=sum(m.aggregate for m in metrics)/len(metrics)
    if aggregate<aggregate_floor:blockers.append("aggregate_below_floor")
    return BenchmarkReport("BLOCKED" if blockers else "PASS",metrics,round(aggregate,6),
                           tuple(sorted(set(blockers))),True,False)
