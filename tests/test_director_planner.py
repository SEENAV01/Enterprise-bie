import unittest
from dataclasses import replace
from bie.game_engine.director_engine.planner import plan_experience
from tests.director_test_support import ctx
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid(self):
  out=plan_experience(ctx());self.assertIsNotNone(out)
 def test_deterministic(self):self.assertEqual(plan_experience(ctx()),plan_experience(ctx()))
 def test_missing_selected_strategy_or_provenance_fails(self):
  c=ctx();bad=replace(c,provenance=replace(c.provenance,refs=()))
  with self.assertRaises(GameContractError):plan_experience(bad)
 def test_product_acceptance_not_present_as_true(self):self.assertNotIn('product_accepted=True',repr(plan_experience(ctx())))

 def test_complete_plan_studio_quality(self):
  p=plan_experience(ctx());self.assertTrue(p.studio_grade_target);self.assertTrue(p.anti_slide_default);self.assertFalse(p.product_accepted)
 def test_deterministic_plan_fingerprint(self):self.assertEqual(plan_experience(ctx()).plan_fingerprint,plan_experience(ctx()).plan_fingerprint)

if __name__=='__main__':unittest.main()
