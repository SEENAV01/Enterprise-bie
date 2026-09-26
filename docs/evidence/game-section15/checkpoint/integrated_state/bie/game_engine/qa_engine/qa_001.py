from __future__ import annotations
from .contracts import *
from .common import *
from .policy import GameQAPolicy

def evaluate(expected_objectives,plans,provenance,policy=GameQAPolicy()):
    policy.validate();expected={o.objective_id for o in expected_objectives};assigned=set();interactive=set();mastery=set();strategies=set();findings=[]
    for p in plans:
        p.validate();strategies.add(p.selected_strategy.value);assigned.update(x.objective_id for x in p.objective_assignments);interactive.update(x.objective_id for x in p.objective_assignments if x.required_interaction);mastery.update(x.objective_id for x in p.mastery_targets)
    cov=ratio(len(expected&assigned),len(expected));icov=ratio(len(expected&interactive),len(expected));mcov=ratio(len(expected&mastery),len(expected))
    for i,(code,val,need) in enumerate((('LEARNING_COVERAGE',cov,policy.learning_coverage_min),('INTERACTIVE_COVERAGE',icov,policy.interactive_coverage_min),('MASTERY_COVERAGE',mcov,policy.mastery_coverage_min)),1):
        if val<need:findings.append(finding('BIE-GAME-QA-001',i,code,f'{code}={val:.3f} below {need:.3f}',refs=provenance_refs(provenance)))
    if expected-assigned:findings.append(finding('BIE-GAME-QA-001',10,'OBJECTIVES_MISSING',','.join(sorted(expected-assigned)),refs=provenance_refs(provenance)))
    metrics=(QualityMetric('learning_coverage',cov,policy.learning_coverage_min,1),QualityMetric('interactive_coverage',icov,policy.interactive_coverage_min,1),QualityMetric('mastery_coverage',mcov,policy.mastery_coverage_min,1),QualityMetric('strategy_diversity',float(len(strategies)),1,None,'count'))
    return result('BIE-GAME-QA-001',{'expected':sorted(expected),'plans':[p.plan_fingerprint for p in plans]},min(cov,icov,mcov),metrics,findings,provenance_refs(provenance))
