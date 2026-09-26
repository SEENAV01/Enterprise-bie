from __future__ import annotations
from .contracts import DirectorContext, MechanicKind
from ..errors import GameContractError
from ..strategy_engine.contracts import StrategyKind

MECHANIC_FOR_STRATEGY={
 StrategyKind.RETRIEVAL:MechanicKind.RETRIEVAL,StrategyKind.MANIPULATION:MechanicKind.MANIPULATE,StrategyKind.SIMULATION:MechanicKind.SIMULATION,
 StrategyKind.PREDICTION:MechanicKind.PREDICT,StrategyKind.DIAGNOSTIC:MechanicKind.DIAGNOSE,StrategyKind.TIMELINE:MechanicKind.TIMELINE,
 StrategyKind.MAP:MechanicKind.MAP,StrategyKind.EQUATION:MechanicKind.EQUATION,StrategyKind.CAUSAL_SYSTEM:MechanicKind.CAUSAL}

def selected_assessment(ctx:DirectorContext):
    ctx.validate();primary=ctx.decision.primary
    matches=[a for a in ctx.decision.ranked if a.strategy is primary]
    if len(matches)!=1:raise GameContractError('GAME_DIR_SELECTED_ASSESSMENT_MISSING')
    a=matches[0]
    if not a.eligible:raise GameContractError('GAME_DIR_SELECTED_STRATEGY_INELIGIBLE')
    return a

def objective_map(ctx):return {o.objective_id:o for o in ctx.signals.objectives}
def mastery_map(ctx):return {m.objective_id:m for m in ctx.mastery}
