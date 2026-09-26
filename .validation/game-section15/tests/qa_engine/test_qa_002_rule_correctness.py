import unittest
from dataclasses import replace
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_002 import evaluate
class Tests(unittest.TestCase):
 def good(self):return evaluate(sample_document(),compiled_bundle())
 def test_pass(self):assert_pass(self,self.good())
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
 def test_full_rule_coverage(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='rule_compile_coverage'),1)
 def test_missing_rule_artifact_fails(self):
  b=compiled_bundle();b2=replace(b,artifacts=tuple(a for a in b.artifacts if a.path!='runtime/rules.ts'));r=evaluate(sample_document(),b2);self.assertIs(r.status,GateStatus.FAIL)
 def test_no_unsafe_eval(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='unsafe_dynamic_execution'),0)
 def test_no_ungrounded(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='ungrounded_rules'),0)
 def test_product_not_accepted(self):self.assertFalse(self.good().product_accepted)
