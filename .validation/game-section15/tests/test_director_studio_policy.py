import unittest
from dataclasses import replace
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.director_engine.studio_policy import audit_studio_quality
from bie.game_engine.errors import GameContractError
class Tests(unittest.TestCase):
 def test_valid_plan_passes_all_policy_checks(self):
  r=audit_studio_quality(plan_experience(director_context()));self.assertTrue(r.passed);self.assertTrue(all(v for _,v in r.checks))
 def test_policy_deterministic(self):self.assertEqual(audit_studio_quality(plan_experience(director_context())),audit_studio_quality(plan_experience(director_context())))
 def test_remove_accessibility_requirement_fails(self):
  p=plan_experience(director_context());m=replace(p.mechanic_assignments[0],accessibility_requirements=());p=replace(p,mechanic_assignments=(m,))
  with self.assertRaisesRegex(GameContractError,'STUDIO_POLICY_FAILED'):audit_studio_quality(p)
 def test_remove_motion_requirement_fails_dynamic(self):
  p=plan_experience(director_context());m=replace(p.mechanic_assignments[0],motion_requirements=());p=replace(p,mechanic_assignments=(m,))
  with self.assertRaisesRegex(GameContractError,'STUDIO_POLICY_FAILED'):audit_studio_quality(p)
 def test_speed_pressure_cannot_pass_policy(self):
  p=plan_experience(director_context());
  with self.assertRaises(GameContractError):replace(p.scoring,speed_bonus_enabled=True).validate()
