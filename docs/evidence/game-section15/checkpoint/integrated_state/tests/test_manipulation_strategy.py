import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.manipulation import assess
from tests.strategy_test_support import bundle,missing_runtime
class ManipulationStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.MANIPULATION)).eligible)
    def test_requires_motion(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.MANIPULATION),'semantic_motion')).eligible)
    def test_requires_accessibility(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.MANIPULATION),'accessibility_keyboard')).eligible)
    def test_visible_effect_strength(self):self.assertIn('visible_cause_effect',assess(bundle(StrategyKind.MANIPULATION)).strengths)
    def test_bounded_reversible_contract(self):
        b=bundle(StrategyKind.MANIPULATION);bad=replace(b.manipulations[0],bounded=False)
        with self.assertRaises(GameContractError):assess(replace(b,manipulations=(bad,)))
    def test_no_signals_blocks(self):self.assertFalse(assess(replace(bundle(StrategyKind.MANIPULATION),manipulations=())).eligible)
    def test_studio_requirement(self):self.assertIn('learner_controls_semantic_objects_not_ui_chrome',assess(bundle(StrategyKind.MANIPULATION)).studio_design_requirements)
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.MANIPULATION)),assess(bundle(StrategyKind.MANIPULATION)))
if __name__=='__main__':unittest.main()
