from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.errors import GameContractError

def ctx(kind=StrategyKind.MANIPULATION):return director_context(kind)
