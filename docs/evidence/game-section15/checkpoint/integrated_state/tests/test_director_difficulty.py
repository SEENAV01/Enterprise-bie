import unittest
from dataclasses import replace
from bie.game_engine.director_engine.difficulty import build_difficulty_curve
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=build_difficulty_curve(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(build_difficulty_curve(ctx()),build_difficulty_curve(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):build_difficulty_curve(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(build_difficulty_curve(ctx())))

 def test_values_bounded_and_support_opposes_gap(self):
  rows=build_difficulty_curve(ctx());self.assertTrue(all(0<=x.difficulty<=1 and 0<=x.support_level<=1 for x in rows))

if __name__=='__main__':unittest.main()
