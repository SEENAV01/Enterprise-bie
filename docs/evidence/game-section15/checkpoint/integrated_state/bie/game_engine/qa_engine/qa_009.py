from __future__ import annotations
from .contracts import *
from .common import *
from .policy import GameQAPolicy
from .candidate import CandidateBenchmarkRecord

def evaluate(cases,policy=GameQAPolicy()):
    policy.validate();cases=tuple(cases);findings=[];rows=[];sigs=[]
    if not cases:raise ValueError('candidate benchmark evidence required')
    for c in cases:c.validate()
    if len(cases)<policy.min_benchmark_domains:findings.append(finding('BIE-GAME-QA-009',1,'BENCHMARK_DOMAIN_COUNT','insufficient benchmark domains',refs=tuple(r for c in cases for r in c.evidence_refs)))
    for c in cases:
        sig=(c.strategy,c.mechanics);sigs.append(sig);ok=c.expected_mechanic in c.mechanics
        rows.append({'domain':c.domain,'strategy':c.strategy,'mechanics':c.mechanics,'expected':c.expected_mechanic,'matched':ok,'plan_fingerprint':c.plan_fingerprint,'document_fingerprint':c.document_fingerprint})
        if not ok:findings.append(finding('BIE-GAME-QA-009',len(findings)+2,'DOMAIN_MECHANIC_MISMATCH',c.domain+':'+','.join(c.mechanics),refs=c.evidence_refs))
    diversity=len({c.strategy for c in cases});clone_ratio=1-(len(set(sigs))/len(sigs))
    if diversity<policy.min_benchmark_strategy_kinds:findings.append(finding('BIE-GAME-QA-009',90,'BENCHMARK_STRATEGY_DIVERSITY',str(diversity)))
    if clone_ratio>policy.max_clone_ratio:findings.append(finding('BIE-GAME-QA-009',91,'TEMPLATE_CLONE_RATIO_HIGH',f'{clone_ratio:.3f}'))
    match=ratio(sum(r['matched'] for r in rows),len(rows));score=min(match,1-clone_ratio);metrics=(QualityMetric('domain_match',match,1,1),QualityMetric('strategy_kinds',float(diversity),float(policy.min_benchmark_strategy_kinds),None,'count'),QualityMetric('clone_ratio',clone_ratio,0,policy.max_clone_ratio))
    refs=tuple(sorted({r for c in cases for r in c.evidence_refs}))
    return result('BIE-GAME-QA-009',rows,score,metrics,findings,refs)
