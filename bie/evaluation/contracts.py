from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

class EvaluationContractError(ValueError):
    pass

@dataclass(frozen=True)
class MetricSpec:
    metric_id:str
    weight:float
    minimum_score:float
    critical:bool=False
    required_evidence_count:int=1

    def validate(self)->None:
        if not self.metric_id:
            raise EvaluationContractError("metric_id required")
        if not 0.0 < self.weight:
            raise EvaluationContractError("metric weight must be > 0")
        if not 0.0 <= self.minimum_score <= 1.0:
            raise EvaluationContractError("minimum_score must be in [0,1]")
        if self.required_evidence_count < 0:
            raise EvaluationContractError("required_evidence_count cannot be negative")
        if self.critical and self.required_evidence_count < 1:
            raise EvaluationContractError("critical metric requires evidence")

@dataclass(frozen=True)
class BenchmarkCase:
    case_id:str
    title:str
    domain:str
    benchmark_version:str
    source_fixture_ref:str
    concept_tags:List[str]
    metrics:List[MetricSpec]
    case_threshold:float
    required:bool=True
    expected_properties:Dict[str,object]=field(default_factory=dict)
    forbidden_properties:List[str]=field(default_factory=list)

    def validate(self)->None:
        if not self.case_id or not self.title or not self.domain:
            raise EvaluationContractError("case identity required")
        if not self.source_fixture_ref:
            raise EvaluationContractError("source fixture required")
        if not self.metrics:
            raise EvaluationContractError("benchmark case requires metrics")
        ids=[m.metric_id for m in self.metrics]
        if len(ids)!=len(set(ids)):
            raise EvaluationContractError("duplicate metric_id")
        for m in self.metrics:m.validate()
        if not 0.0 <= self.case_threshold <= 1.0:
            raise EvaluationContractError("case threshold must be in [0,1]")

@dataclass(frozen=True)
class MetricEvidence:
    metric_id:str
    score:float
    evaluator:str
    evaluator_version:str
    evidence_refs:List[str]
    notes:str=""

    def validate(self)->None:
        if not self.metric_id:
            raise EvaluationContractError("metric_id required")
        if not 0.0 <= self.score <= 1.0:
            raise EvaluationContractError("metric score must be in [0,1]")
        if not self.evaluator or not self.evaluator_version:
            raise EvaluationContractError("evaluator identity required")

@dataclass(frozen=True)
class CaseResult:
    case_id:str
    status:str
    weighted_score:float
    metric_scores:Dict[str,float]
    failed_metrics:List[str]
    missing_evidence_metrics:List[str]

@dataclass(frozen=True)
class DomainRequirement:
    domain:str
    minimum_score:float
    required_case_count:int=1

    def validate(self)->None:
        if not self.domain:
            raise EvaluationContractError("domain required")
        if not 0.0 <= self.minimum_score <= 1.0:
            raise EvaluationContractError("domain minimum score must be [0,1]")
        if self.required_case_count < 1:
            raise EvaluationContractError("required_case_count must be >=1")

@dataclass(frozen=True)
class BenchmarkSuite:
    suite_id:str
    suite_version:str
    cases:List[BenchmarkCase]
    domain_requirements:List[DomainRequirement]
    global_threshold:float

    def validate(self)->None:
        if not self.suite_id or not self.suite_version:
            raise EvaluationContractError("suite identity required")
        if not self.cases:
            raise EvaluationContractError("suite requires cases")
        case_ids=[c.case_id for c in self.cases]
        if len(case_ids)!=len(set(case_ids)):
            raise EvaluationContractError("duplicate case_id")
        for c in self.cases:c.validate()
        domains={c.domain for c in self.cases if c.required}
        for d in self.domain_requirements:
            d.validate()
            if d.domain not in domains:
                raise EvaluationContractError(f"domain requirement has no required case: {d.domain}")
            count=sum(1 for c in self.cases if c.required and c.domain==d.domain)
            if count < d.required_case_count:
                raise EvaluationContractError(f"domain {d.domain} lacks required case count")
        if not 0.0 <= self.global_threshold <= 1.0:
            raise EvaluationContractError("global threshold must be [0,1]")

@dataclass(frozen=True)
class SuiteResult:
    suite_id:str
    status:str
    global_score:float
    domain_scores:Dict[str,float]
    failed_cases:List[str]
    domain_failures:List[str]

class BenchmarkEvaluator:
    @staticmethod
    def evaluate_case(case:BenchmarkCase, evidence:List[MetricEvidence])->CaseResult:
        case.validate()
        for e in evidence:e.validate()
        by:Dict[str,List[MetricEvidence]]={}
        for e in evidence:
            by.setdefault(e.metric_id,[]).append(e)

        failed=[]
        missing=[]
        metric_scores={}
        weighted_sum=0.0
        total_weight=0.0

        for spec in case.metrics:
            evs=by.get(spec.metric_id,[])
            if len(evs) < spec.required_evidence_count:
                missing.append(spec.metric_id)
                metric_scores[spec.metric_id]=0.0
                if spec.critical:
                    failed.append(spec.metric_id)
                total_weight += spec.weight
                continue

            # Conservative aggregation: lowest score across evidence sources.
            score=min(e.score for e in evs)
            metric_scores[spec.metric_id]=score
            weighted_sum += score*spec.weight
            total_weight += spec.weight

            if score < spec.minimum_score:
                failed.append(spec.metric_id)

        weighted_score=weighted_sum/total_weight if total_weight else 0.0
        status="PASS"
        if missing or failed or weighted_score < case.case_threshold:
            status="FAIL"

        return CaseResult(
            case_id=case.case_id,
            status=status,
            weighted_score=round(weighted_score,4),
            metric_scores=metric_scores,
            failed_metrics=sorted(set(failed)),
            missing_evidence_metrics=sorted(set(missing)),
        )

    @staticmethod
    def evaluate_suite(
        suite:BenchmarkSuite,
        case_results:List[CaseResult]
    )->SuiteResult:
        suite.validate()
        by={r.case_id:r for r in case_results}
        failed_cases=[]
        for c in suite.cases:
            if c.required:
                if c.case_id not in by or by[c.case_id].status!="PASS":
                    failed_cases.append(c.case_id)

        domain_scores={}
        domain_failures=[]
        for req in suite.domain_requirements:
            results=[by[c.case_id] for c in suite.cases
                     if c.required and c.domain==req.domain and c.case_id in by]
            if len(results)<req.required_case_count:
                domain_scores[req.domain]=0.0
                domain_failures.append(req.domain)
                continue
            score=sum(r.weighted_score for r in results)/len(results)
            domain_scores[req.domain]=round(score,4)
            if score < req.minimum_score:
                domain_failures.append(req.domain)

        required_results=[by[c.case_id] for c in suite.cases if c.required and c.case_id in by]
        global_score=(sum(r.weighted_score for r in required_results)/len(required_results)
                      if required_results else 0.0)

        status="PASS"
        if failed_cases or domain_failures or global_score<suite.global_threshold:
            status="FAIL"

        return SuiteResult(
            suite_id=suite.suite_id,
            status=status,
            global_score=round(global_score,4),
            domain_scores=domain_scores,
            failed_cases=sorted(set(failed_cases)),
            domain_failures=sorted(set(domain_failures)),
        )
