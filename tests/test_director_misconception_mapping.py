import unittest
from dataclasses import replace
from bie.game_engine.director_engine.misconception_mapping import map_misconceptions
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=map_misconceptions(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(map_misconceptions(ctx()),map_misconceptions(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):map_misconceptions(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(map_misconceptions(ctx())))

 def test_no_misconception_returns_empty_without_fabrication(self):self.assertEqual(map_misconceptions(ctx()),())

if __name__=='__main__':unittest.main()
