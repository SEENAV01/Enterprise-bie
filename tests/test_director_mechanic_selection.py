import unittest
from dataclasses import replace
from bie.game_engine.director_engine.mechanic_selection import select_mechanics
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=select_mechanics(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(select_mechanics(ctx()),select_mechanics(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):select_mechanics(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(select_mechanics(ctx())))

 def test_all_strategy_kinds_map_to_distinct_governed_mechanics(self):
  from bie.game_engine.strategy_engine.contracts import StrategyKind
  seen=set()
  for k in StrategyKind:seen.add(tuple(x.mechanic.value for x in select_mechanics(ctx(k))))
  self.assertGreaterEqual(len(seen),8)
 def test_runtime_capability_missing_fails(self):
  from dataclasses import replace
  from bie.game_engine.strategy_engine.contracts import RuntimeCapabilitySet
  c=ctx();c=replace(c,signals=replace(c.signals,runtime=replace(c.signals.runtime,semantic_motion=False)))
  with self.assertRaises(GameContractError):select_mechanics(c)

if __name__=='__main__':unittest.main()
