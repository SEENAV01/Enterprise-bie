import unittest
from dataclasses import replace
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.causal_system import assess
from tests.strategy_test_support import bundle,missing_runtime
class CausalStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.CAUSAL_SYSTEM)).eligible)
    def test_no_edges_blocks(self):self.assertFalse(assess(replace(bundle(StrategyKind.CAUSAL_SYSTEM),causal_edges=())).eligible)
    def test_graph_runtime_required(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.CAUSAL_SYSTEM),'graph_runtime')).eligible)
    def test_branching_runtime_required(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.CAUSAL_SYSTEM),'branching_runtime')).eligible)
    def test_correlation_warning(self):self.assertIn('distinguish_correlation_from_causation',assess(bundle(StrategyKind.CAUSAL_SYSTEM)).studio_design_requirements)
    def test_never_infer_edge(self):self.assertIn('never_infer_unproven_causal_edge',assess(bundle(StrategyKind.CAUSAL_SYSTEM)).studio_design_requirements)
    def test_evidence_score_not_perfect_if_edge_strength_less_than_one(self):self.assertLess(assess(bundle(StrategyKind.CAUSAL_SYSTEM)).score,100)
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.CAUSAL_SYSTEM)),assess(bundle(StrategyKind.CAUSAL_SYSTEM)))
if __name__=='__main__':unittest.main()
