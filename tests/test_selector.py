import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.strategy_engine.contracts import StrategyKind, StrategyPolicy, DecisionStatus
from bie.game_engine.strategy_engine.fixtures import rich_bundle, single_strategy_bundle
from bie.game_engine.strategy_engine.selector import assess_all_strategies,select_revision_strategy,select_or_raise
class SelectorTests(unittest.TestCase):
    def test_assesses_all_nine(self):self.assertEqual(len(assess_all_strategies(rich_bundle())),9)
    def test_single_strategy_selects(self):
        d=select_revision_strategy(single_strategy_bundle(StrategyKind.MANIPULATION));self.assertEqual(d.status,DecisionStatus.SELECTED);self.assertEqual(d.primary,StrategyKind.MANIPULATION)
    def test_rich_bundle_ambiguous_abstains(self):self.assertEqual(select_revision_strategy(rich_bundle()).status,DecisionStatus.ABSTAIN_AMBIGUOUS)
    def test_select_or_raise_on_ambiguity(self):
        with self.assertRaisesRegex(GameContractError,'SELECTION_ABSTAIN'):select_or_raise(rich_bundle())
    def test_high_threshold_can_abstain(self):
        d=select_revision_strategy(single_strategy_bundle(StrategyKind.CAUSAL_SYSTEM),StrategyPolicy(minimum_score=99.9));self.assertEqual(d.status,DecisionStatus.ABSTAIN_BELOW_THRESHOLD)
    def test_runtime_loss_can_remove_candidate(self):
        b=single_strategy_bundle(StrategyKind.MANIPULATION);b=replace(b,runtime=replace(b.runtime,semantic_motion=False));self.assertEqual(select_revision_strategy(b).status,DecisionStatus.ABSTAIN_NO_ELIGIBLE)
    def test_ranking_deterministic(self):self.assertEqual(select_revision_strategy(rich_bundle()),select_revision_strategy(rich_bundle()))
    def test_fingerprint_stable(self):self.assertEqual(select_revision_strategy(rich_bundle()).decision_fingerprint,select_revision_strategy(rich_bundle()).decision_fingerprint)
    def test_no_product_acceptance(self):self.assertFalse(select_revision_strategy(single_strategy_bundle(StrategyKind.RETRIEVAL)).product_accepted)
    def test_policy_validation(self):
        with self.assertRaises(GameContractError):select_revision_strategy(single_strategy_bundle(StrategyKind.RETRIEVAL),StrategyPolicy(minimum_score=101))
    def test_rank_order_stable_on_tie(self):
        d=select_revision_strategy(rich_bundle()); names=[a.strategy.value for a in d.ranked];self.assertEqual(names,sorted(names,key=lambda n:(-next(x.score for x in d.ranked if x.strategy.value==n),-next(x.confidence for x in d.ranked if x.strategy.value==n),n)))
    def test_selected_rationale_has_score(self):self.assertIn('score=',select_revision_strategy(single_strategy_bundle(StrategyKind.EQUATION)).rationale[1])
if __name__=='__main__':unittest.main()
