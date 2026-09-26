import unittest
from dataclasses import replace
from bie.game_engine.director_engine.scoring import design_scoring
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=design_scoring(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(design_scoring(ctx()),design_scoring(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):design_scoring(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(design_scoring(ctx())))

 def test_mastery_not_speed_drives_score(self):
  p=design_scoring(ctx());self.assertTrue(p.mastery_weighted);self.assertFalse(p.speed_bonus_enabled)

if __name__=='__main__':unittest.main()
