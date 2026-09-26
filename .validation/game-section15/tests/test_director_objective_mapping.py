import unittest
from dataclasses import replace
from bie.game_engine.director_engine.objective_mapping import map_objectives
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=map_objectives(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(map_objectives(ctx()),map_objectives(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):map_objectives(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(map_objectives(ctx())))

 def test_full_objective_coverage(self):
  c=ctx();self.assertEqual({x.objective_id for x in map_objectives(c)},{x.objective_id for x in c.signals.objectives})

if __name__=='__main__':unittest.main()
