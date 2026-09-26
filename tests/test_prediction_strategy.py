import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.prediction import assess
from tests.strategy_test_support import bundle,missing_runtime
class PredictionStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.PREDICTION)).eligible)
    def test_precommit_contract(self):
        b=bundle(StrategyKind.PREDICTION);bad=replace(b.predictions[0],commitment_before_observation=False)
        with self.assertRaises(GameContractError):assess(replace(b,predictions=(bad,)))
    def test_missing_motion_blocks(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.PREDICTION),'semantic_motion')).eligible)
    def test_no_signal_blocks(self):self.assertFalse(assess(replace(bundle(StrategyKind.PREDICTION),predictions=())).eligible)
    def test_visual_comparison_required(self):self.assertIn('compare_prediction_vs_outcome_visually',assess(bundle(StrategyKind.PREDICTION)).studio_design_requirements)
    def test_feedback_not_correctness_only(self):self.assertIn('feedback_explains_model_not_just_correctness',assess(bundle(StrategyKind.PREDICTION)).studio_design_requirements)
    def test_score(self):self.assertGreaterEqual(assess(bundle(StrategyKind.PREDICTION)).score,80)
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.PREDICTION)),assess(bundle(StrategyKind.PREDICTION)))
if __name__=='__main__':unittest.main()
