import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.director_engine.fixtures import director_context
from bie.game_engine.director_engine.planner import plan_experience
from bie.game_engine.director_engine.hint_strategy import design_hints
from bie.game_engine.director_engine.feedback_design import design_feedback
from bie.game_engine.director_engine.scoring import design_scoring
from bie.game_engine.director_engine.adaptation import design_adaptation
from bie.game_engine.director_engine.difficulty import build_difficulty_curve

class ConsistencyTests(unittest.TestCase):
    def setUp(self):self.ctx=director_context();self.plan=plan_experience(self.ctx)
    def test_plan_fingerprint_stable(self):self.assertEqual(self.plan.plan_fingerprint,plan_experience(self.ctx).plan_fingerprint)
    def test_remove_mechanic_breaks_validation(self):
        with self.assertRaises(GameContractError):replace(self.plan,mechanic_assignments=()).validate()
    def test_duplicate_objective_breaks_validation(self):
        with self.assertRaises(GameContractError):replace(self.plan,objective_assignments=self.plan.objective_assignments*2).validate()
    def test_difficulty_matches_level_ids(self):self.assertEqual({x.level_id for x in self.plan.difficulty},{x.level_id for x in self.plan.levels})
    def test_hint_coverage_matches_objectives(self):self.assertEqual({x.objective_id for x in self.plan.hints},{x.objective_id for x in self.plan.objective_assignments})
    def test_adaptation_coverage_matches_objectives(self):self.assertEqual({x.objective_id for x in self.plan.adaptations},{x.objective_id for x in self.plan.objective_assignments})
    def test_hints_never_reveal_full_answer(self):self.assertTrue(all(x.reveal_fraction<1 for x in design_hints(self.ctx)))
    def test_feedback_never_reveals_before_attempt(self):self.assertTrue(all(not x.answer_reveal_before_attempt for x in design_feedback(self.ctx)))
    def test_scoring_has_no_speed_pressure(self):self.assertFalse(design_scoring(self.ctx).speed_bonus_enabled)
    def test_adaptation_priorities_stable(self):
        rows=design_adaptation(self.ctx);self.assertEqual([x.priority for x in rows],sorted(x.priority for x in rows))
    def test_level_durations_within_contract(self):self.assertTrue(all(self.ctx.constraints.minimum_interaction_seconds<=x.estimated_seconds<=self.ctx.constraints.max_level_seconds for x in self.plan.levels))
    def test_difficulty_is_bounded(self):self.assertTrue(all(0<=x.difficulty<=1 and 0<=x.cognitive_load<=1 and 0<=x.support_level<=1 for x in build_difficulty_curve(self.ctx)))
