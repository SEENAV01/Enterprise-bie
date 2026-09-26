from __future__ import annotations
from .contracts import MasterySignal,DirectorConstraints,DirectorContext
from ..strategy_engine.fixtures import single_strategy_bundle
from ..strategy_engine.contracts import StrategyKind
from ..strategy_engine.selector import select_or_raise

def director_context(kind=StrategyKind.MANIPULATION):
    b=single_strategy_bundle(kind);d=select_or_raise(b);ms=tuple(MasterySignal(o.objective_id,.35,.85,2,o.provenance) for o in b.objectives)
    return DirectorContext(b,d,ms,DirectorConstraints(),b.provenance).validate()
