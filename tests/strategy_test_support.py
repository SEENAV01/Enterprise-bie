from dataclasses import replace
from bie.game_engine.strategy_engine.contracts import StrategyKind, RuntimeCapabilitySet
from bie.game_engine.strategy_engine.fixtures import single_strategy_bundle

def bundle(kind):return single_strategy_bundle(kind)
def missing_runtime(b,name):return replace(b,runtime=replace(b.runtime,**{name:False}))
