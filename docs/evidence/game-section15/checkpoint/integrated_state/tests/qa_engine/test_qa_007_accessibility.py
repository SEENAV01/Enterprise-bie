import unittest
from dataclasses import replace
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_007 import evaluate
class Tests(unittest.TestCase):
 def good(self):return evaluate(sample_document(),compiled_bundle(),runtime_result().browser)
 def test_pass(self):assert_pass(self,self.good())
 def test_contract_coverage_full(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='accessibility_contract_coverage'),1)
 def test_semantic_entities_present(self):self.assertGreaterEqual(next(m.value for m in self.good().metrics if m.name=='semantic_entities'),1)
 def test_slide_deck_browser_fails(self):self.assertIs(evaluate(sample_document(),compiled_bundle(),replace(runtime_result().browser,slide_deck=True)).status,GateStatus.FAIL)
 def test_missing_interaction_artifact_fails(self):
  b=compiled_bundle();b=replace(b,artifacts=tuple(a for a in b.artifacts if a.path!='runtime/interactions.ts'));self.assertIs(evaluate(sample_document(),b,runtime_result().browser).status,GateStatus.FAIL)
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
 def test_product_not_accepted(self):self.assertFalse(self.good().product_accepted)
