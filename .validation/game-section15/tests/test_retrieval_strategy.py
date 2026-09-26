import unittest
from dataclasses import replace
from bie.game_engine.strategy_engine.contracts import StrategyKind
from bie.game_engine.strategy_engine.retrieval import assess
from tests.strategy_test_support import bundle,missing_runtime
class RetrievalStrategyTests(unittest.TestCase):
    def test_eligible(self): self.assertTrue(assess(bundle(StrategyKind.RETRIEVAL)).eligible)
    def test_high_score(self): self.assertGreaterEqual(assess(bundle(StrategyKind.RETRIEVAL)).score,80)
    def test_no_items_blocks(self): self.assertFalse(assess(replace(bundle(StrategyKind.RETRIEVAL),retrieval_items=())).eligible)
    def test_missing_runtime_blocks(self): self.assertFalse(assess(missing_runtime(bundle(StrategyKind.RETRIEVAL),'audio_feedback')).eligible)
    def test_design_forbids_mcq_core(self): self.assertIn('no_mcq_only_core_gameplay',assess(bundle(StrategyKind.RETRIEVAL)).studio_design_requirements)
    def test_evidence_present(self): self.assertTrue(assess(bundle(StrategyKind.RETRIEVAL)).evidence_refs)
    def test_deterministic(self): self.assertEqual(assess(bundle(StrategyKind.RETRIEVAL)),assess(bundle(StrategyKind.RETRIEVAL)))
    def test_duplicate_prompt_blocks(self):
        b=bundle(StrategyKind.RETRIEVAL); x=replace(b.retrieval_items[1],prompt_ref=b.retrieval_items[0].prompt_ref);self.assertFalse(assess(replace(b,retrieval_items=(b.retrieval_items[0],x))).eligible)
if __name__=='__main__':unittest.main()
