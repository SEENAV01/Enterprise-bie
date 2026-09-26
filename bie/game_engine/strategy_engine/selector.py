from __future__ import annotations
from .contracts import StrategyKind, StrategyPolicy, StrategyDecision, DecisionStatus
from . import retrieval, manipulation, simulation, prediction, diagnostic, timeline, map_strategy, equation, causal_system
from ..errors import GameContractError
from ..canonical import fingerprint

ASSESSORS={
 StrategyKind.RETRIEVAL:retrieval.assess, StrategyKind.MANIPULATION:manipulation.assess, StrategyKind.SIMULATION:simulation.assess,
 StrategyKind.PREDICTION:prediction.assess, StrategyKind.DIAGNOSTIC:diagnostic.assess, StrategyKind.TIMELINE:timeline.assess,
 StrategyKind.MAP:map_strategy.assess, StrategyKind.EQUATION:equation.assess, StrategyKind.CAUSAL_SYSTEM:causal_system.assess,
}

def assess_all_strategies(bundle):
    bundle.validate();return tuple(ASSESSORS[k](bundle) for k in StrategyKind)

def select_revision_strategy(bundle, policy=StrategyPolicy()):
    bundle.validate();policy.validate();assessments=assess_all_strategies(bundle)
    ranked=tuple(sorted(assessments,key=lambda a:(-a.score,-a.confidence,a.strategy.value)))
    eligible=[a for a in ranked if a.eligible and a.score>=policy.minimum_score and a.confidence>=policy.minimum_confidence]
    if not eligible:
        any_eligible=any(a.eligible for a in ranked)
        status=DecisionStatus.ABSTAIN_BELOW_THRESHOLD if any_eligible else DecisionStatus.ABSTAIN_NO_ELIGIBLE
        rationale=('No strategy satisfied governed score/confidence thresholds.',) if any_eligible else ('No strategy passed capability and evidence eligibility gates.',)
        material={'status':status.value,'ranked':[(a.strategy.value,a.score,a.confidence,a.eligible) for a in ranked]}
        return StrategyDecision(status,None,None,ranked,rationale,fingerprint(material),False).validate()
    top=eligible[0];second=eligible[1] if len(eligible)>1 else None
    if second is not None and top.score-second.score < policy.ambiguity_margin:
        material={'status':DecisionStatus.ABSTAIN_AMBIGUOUS.value,'top':top.strategy.value,'second':second.strategy.value,'scores':[top.score,second.score]}
        return StrategyDecision(DecisionStatus.ABSTAIN_AMBIGUOUS,None,None,ranked,(f'Top strategies are within ambiguity margin {policy.ambiguity_margin}.','Director/human or stronger evidence must resolve the strategy choice.'),fingerprint(material),False).validate()
    secondary=None
    if policy.allow_secondary_recommendation and second is not None and top.score-second.score>=policy.ambiguity_margin and second.score>=policy.minimum_score:
        secondary=second.strategy
    material={'status':'selected','primary':top.strategy.value,'secondary':secondary.value if secondary else None,'score':top.score,'confidence':top.confidence,'assessment':top.assessment_fingerprint}
    return StrategyDecision(DecisionStatus.SELECTED,top.strategy,secondary,ranked,(f'Selected {top.strategy.value} using structured capability/evidence scoring.',f'Primary score={top.score:.4f}, confidence={top.confidence:.4f}.'),fingerprint(material),False).validate()

def select_or_raise(bundle,policy=StrategyPolicy()):
    decision=select_revision_strategy(bundle,policy)
    if decision.status is not DecisionStatus.SELECTED:raise GameContractError('GAME_STRATEGY_SELECTION_ABSTAIN',decision.status.value)
    return decision
