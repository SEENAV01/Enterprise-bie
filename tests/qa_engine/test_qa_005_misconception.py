import unittest
from dataclasses import replace
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_005 import evaluate
class Tests(unittest.TestCase):
 def pair(self):return single_strategy_bundle(StrategyKind.DIAGNOSTIC),diagnostic_plan()
 def good(self):b,p=self.pair();return evaluate(b,p)
 def test_pass(self):assert_pass(self,self.good())
 def test_alignment_full(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='misconception_alignment'),1)
 def test_missing_mapping_fails(self):
  b,p=self.pair();p=replace(p,misconception_assignments=());self.assertIs(evaluate(b,p).status,GateStatus.FAIL)
 def test_missing_feedback_fails(self):
  b,p=self.pair();p=replace(p,feedback=tuple(replace(x,misconception_refs=()) for x in p.feedback));self.assertIs(evaluate(b,p).status,GateStatus.FAIL)
 def test_missing_remediation_fails(self):
  b,p=self.pair();p=replace(p,adaptations=tuple(a for a in p.adaptations if a.action.value not in ('remediate','easier_variant')));self.assertIs(evaluate(b,p).status,GateStatus.FAIL)
 def test_diagnostic_required(self):
  b,p=self.pair();p=replace(p,misconception_assignments=tuple(replace(x,diagnostic_required=False) for x in p.misconception_assignments));self.assertIs(evaluate(b,p).status,GateStatus.FAIL)
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
