import unittest
from dataclasses import replace
from bie.game_engine.director_engine.mastery_mapping import map_mastery
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=map_mastery(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(map_mastery(ctx()),map_mastery(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):map_mastery(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(map_mastery(ctx())))

 def test_unseen_objective_is_explicit(self):
  from dataclasses import replace
  c=ctx();c=replace(c,mastery=())
  self.assertEqual(map_mastery(c)[0].evidence_state,'unseen')

if __name__=='__main__':unittest.main()
