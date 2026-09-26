import unittest
from dataclasses import replace
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.timeline import assess
from tests.strategy_test_support import bundle,missing_runtime
class TimelineStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.TIMELINE)).eligible)
    def test_requires_two_events(self):
        b=bundle(StrategyKind.TIMELINE);self.assertFalse(assess(replace(b,temporal_events=b.temporal_events[:1])).eligible)
    def test_runtime_required(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.TIMELINE),'timeline_runtime')).eligible)
    def test_keyboard_requirement(self):self.assertIn('support_keyboard_reordering',assess(bundle(StrategyKind.TIMELINE)).studio_design_requirements)
    def test_chronology_causality_separated(self):self.assertIn('show_causal_links_separately_from_chronology',assess(bundle(StrategyKind.TIMELINE)).studio_design_requirements)
    def test_score(self):self.assertGreaterEqual(assess(bundle(StrategyKind.TIMELINE)).score,80)
    def test_coverage(self):self.assertEqual(assess(bundle(StrategyKind.TIMELINE)).objective_coverage,('obj:time',))
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.TIMELINE)),assess(bundle(StrategyKind.TIMELINE)))
if __name__=='__main__':unittest.main()
