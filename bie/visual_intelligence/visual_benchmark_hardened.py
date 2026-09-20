from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping, Sequence
from .realbook_fixtures import RealBookFixture, validate_fixture_pack

class VisualBenchmarkError(ValueError): pass

@dataclass(frozen=True)
class BenchmarkObservation:
    fixture_id:str
    representation:str|None
    grammar:str|None
    concept_coverage:float|None
    relation_coverage:float|None
    grounding_score:float|None
    accessibility_pass:bool|None
    trace_pass:bool|None
    empirical_render_pass:bool|None

@dataclass(frozen=True)
class CaseBenchmarkResult:
    fixture_id:str
    status:str
    score:float|None
    failures:tuple[str,...]
    not_run_checks:tuple[str,...]

@dataclass(frozen=True)
class BenchmarkReport:
    version:str
    results:tuple[CaseBenchmarkResult,...]
    aggregate_score:float|None
    hard_floor_failures:tuple[str,...]
    not_run:bool
    passed:bool
    review_required:bool=True
    accepted:bool=False

def evaluate_case(fixture,obs,*,require_empirical=False):
    if fixture.fixture_id!=obs.fixture_id: raise VisualBenchmarkError("fixture/observation id mismatch")
    failures=[];notrun=[]
    if obs.representation!=fixture.expected_representation: failures.append("representation_mismatch")
    if obs.grammar!=fixture.expected_grammar: failures.append("grammar_mismatch")
    metrics=[]
    for name,value,floor in (
        ("concept_coverage",obs.concept_coverage,.90),
        ("relation_coverage",obs.relation_coverage,.85),
        ("grounding_score",obs.grounding_score,.90),
    ):
        if value is None: notrun.append(name)
        else:
            if not 0<=value<=1: raise VisualBenchmarkError(name+" outside [0,1]")
            metrics.append(value)
            if value<floor: failures.append(name+"_below_floor")
    if obs.accessibility_pass is None: notrun.append("accessibility")
    elif not obs.accessibility_pass: failures.append("accessibility_failed")
    if obs.trace_pass is None: notrun.append("trace")
    elif not obs.trace_pass: failures.append("trace_failed")
    if obs.empirical_render_pass is None:
        if require_empirical: notrun.append("empirical_render")
    elif not obs.empirical_render_pass: failures.append("empirical_render_failed")
    score=sum(metrics)/len(metrics) if metrics else None
    status="FAIL" if failures else ("NOT_RUN" if notrun else "PASS")
    return CaseBenchmarkResult(fixture.fixture_id,status,None if score is None else round(score,6),
                               tuple(sorted(failures)),tuple(sorted(notrun)))

def run_benchmark(fixtures,observations,*,version="1.0.0",require_empirical=False,aggregate_floor=.88):
    validate_fixture_pack(fixtures)
    obs={o.fixture_id:o for o in observations}
    if len(obs)!=len(tuple(observations)): raise VisualBenchmarkError("duplicate observations")
    results=[]
    for f in fixtures:
        if f.fixture_id not in obs:
            results.append(CaseBenchmarkResult(f.fixture_id,"NOT_RUN",None,(),("missing_observation",)))
        else:
            results.append(evaluate_case(f,obs[f.fixture_id],require_empirical=require_empirical))
    scored=[r.score for r in results if r.score is not None]
    aggregate=None if not scored else round(sum(scored)/len(scored),6)
    hard=[]
    for r in results:
        if r.status=="FAIL": hard.append("case_failed:"+r.fixture_id)
    if aggregate is not None and aggregate<aggregate_floor: hard.append("aggregate_below_floor")
    notrun=any(r.status=="NOT_RUN" or r.not_run_checks for r in results)
    passed=not hard and not notrun and aggregate is not None
    return BenchmarkReport(version,tuple(results),aggregate,tuple(sorted(hard)),notrun,passed,True,False)

def adversarial_mutations(fixture):
    return (
        {"fixture_id":fixture.fixture_id,"mutation":"wrong_representation","expected_failure":"representation_mismatch"},
        {"fixture_id":fixture.fixture_id,"mutation":"wrong_grammar","expected_failure":"grammar_mismatch"},
        {"fixture_id":fixture.fixture_id,"mutation":"low_grounding","expected_failure":"grounding_score_below_floor"},
    )
