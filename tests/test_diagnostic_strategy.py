import unittest
from dataclasses import replace
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.diagnostic import assess
from tests.strategy_test_support import bundle,missing_runtime
class DiagnosticStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.DIAGNOSTIC)).eligible)
    def test_no_cases_blocks(self):self.assertFalse(assess(replace(bundle(StrategyKind.DIAGNOSTIC),diagnostics=())).eligible)
    def test_accessibility_required(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.DIAGNOSTIC),'accessibility_keyboard')).eligible)
    def test_misconception_feedback_strength(self):self.assertIn('misconception_specific_feedback',assess(bundle(StrategyKind.DIAGNOSTIC)).strengths)
    def test_no_gotcha_requirement(self):self.assertIn('never_use_gotcha_traps_without_explanation',assess(bundle(StrategyKind.DIAGNOSTIC)).studio_design_requirements)
    def test_score(self):self.assertGreaterEqual(assess(bundle(StrategyKind.DIAGNOSTIC)).score,80)
    def test_evidence(self):self.assertTrue(assess(bundle(StrategyKind.DIAGNOSTIC)).evidence_refs)
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.DIAGNOSTIC)),assess(bundle(StrategyKind.DIAGNOSTIC)))
if __name__=='__main__':unittest.main()
