from __future__ import annotations
from .contracts import ScoreComponent, StrategyAssessment, StrategyKind, assessment_fingerprint
from ..canonical import fingerprint
from ..errors import GameContractError


def weighted_score(components:tuple[ScoreComponent,...])->float:
    if not components:raise GameContractError('GAME_STRATEGY_SCORE_COMPONENTS_REQUIRED')
    total=sum(c.weight for c in components);return round(100*sum(c.value*c.weight for c in components)/total,4)

def confidence_from_evidence(count:int, coverage:float, floor:float=0.45)->float:
    if count<0 or not 0<=coverage<=1:raise GameContractError('GAME_STRATEGY_CONFIDENCE_INPUT')
    return round(min(1.0,floor+0.08*min(count,5)+0.15*coverage),4)

def runtime_blockers(runtime,required:tuple[str,...])->tuple[str,...]:
    return tuple('missing_runtime:'+name for name in required if not runtime.has(name))

def build_assessment(*,strategy:StrategyKind, eligible:bool, components:tuple[ScoreComponent,...], coverage:tuple[str,...], blockers:tuple[str,...], strengths:tuple[str,...], runtime_required:tuple[str,...], design_requirements:tuple[str,...], evidence_refs:tuple[str,...], confidence:float)->StrategyAssessment:
    for c in components:c.validate()
    score=weighted_score(components) if components else 0.0
    if blockers:eligible=False
    material={'strategy':strategy.value,'eligible':eligible,'score':score,'confidence':confidence,'coverage':sorted(coverage),'blockers':sorted(blockers),'strengths':sorted(strengths),'runtime':runtime_required,'design':design_requirements,'evidence':sorted(evidence_refs),'components':[(c.name,c.value,c.weight,c.rationale) for c in components]}
    out=StrategyAssessment(strategy,eligible,score,confidence,tuple(sorted(coverage)),tuple(sorted(blockers)),tuple(sorted(strengths)),runtime_required,design_requirements,tuple(sorted(set(evidence_refs))),components,assessment_fingerprint(material),False)
    return out.validate()

def objective_ids(bundle):return tuple(sorted(x.objective_id for x in bundle.objectives))
def evidence_ids(provenances):
    values=[]
    for p in provenances:
        for r in p.refs:values.append(f'{r.artifact_id}@{r.locator}:{r.role}')
    return tuple(sorted(set(values)))
def fraction(n,d):return 0.0 if d==0 else min(1.0,n/d)
