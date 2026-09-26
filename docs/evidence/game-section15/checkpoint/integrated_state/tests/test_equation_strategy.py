import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.equation import assess
from tests.strategy_test_support import bundle,missing_runtime
class EquationStrategyTests(unittest.TestCase):
    def test_eligible(self):self.assertTrue(assess(bundle(StrategyKind.EQUATION)).eligible)
    def test_invariant_required(self):
        b=bundle(StrategyKind.EQUATION);bad=replace(b.equations[0],equivalence_invariant=False)
        with self.assertRaises(GameContractError):assess(replace(b,equations=(bad,)))
    def test_symbolic_runtime_required(self):self.assertFalse(assess(missing_runtime(bundle(StrategyKind.EQUATION),'symbolic_math_runtime')).eligible)
    def test_semantic_equation_objects(self):self.assertIn('render_equation_as_semantic_objects_not_flat_text',assess(bundle(StrategyKind.EQUATION)).studio_design_requirements)
    def test_no_eval(self):self.assertIn('never_use_eval_or_string_execution',assess(bundle(StrategyKind.EQUATION)).studio_design_requirements)
    def test_no_signal_blocks(self):self.assertFalse(assess(replace(bundle(StrategyKind.EQUATION),equations=())).eligible)
    def test_score(self):self.assertGreaterEqual(assess(bundle(StrategyKind.EQUATION)).score,80)
    def test_deterministic(self):self.assertEqual(assess(bundle(StrategyKind.EQUATION)),assess(bundle(StrategyKind.EQUATION)))
if __name__=='__main__':unittest.main()
