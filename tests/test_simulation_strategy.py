import unittest
from dataclasses import replace
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.simulation import assess
from tests.strategy_test_support import bundle,missing_runtime
class SimulationStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.SIMULATION)).eligible)
    def test_runtime_required(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.SIMULATION),'simulation_runtime')).eligible)
    def test_scope_strength(self):self.assertIn('declared_model_scope',assess(bundle(StrategyKind.SIMULATION)).strengths)
    def test_no_model_blocks(self):self.assertFalse(assess(replace(bundle(StrategyKind.SIMULATION),simulations=())).eligible)
    def test_motion_requirement(self):self.assertIn('visualize_model_state_continuously',assess(bundle(StrategyKind.SIMULATION)).studio_design_requirements)
    def test_truthfulness_requirement(self):self.assertIn('never_present_simulation_as_unqualified_ground_truth',assess(bundle(StrategyKind.SIMULATION)).studio_design_requirements)
    def test_confidence(self):self.assertGreater(assess(bundle(StrategyKind.SIMULATION)).confidence,.5)
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.SIMULATION)),assess(bundle(StrategyKind.SIMULATION)))
if __name__=='__main__':unittest.main()
