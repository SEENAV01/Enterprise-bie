import unittest
from dataclasses import replace
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_006 import evaluate
from bie.game_engine.compiler_engine.contracts import artifact,ArtifactKind
class Tests(unittest.TestCase):
 def good(self):return evaluate(sample_document(),compiled_bundle())
 def test_pass(self):assert_pass(self,self.good())
 def test_coverage_full(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='feedback_compile_coverage'),1)
 def test_missing_artifact_fails(self):
  b=compiled_bundle();b=replace(b,artifacts=tuple(a for a in b.artifacts if a.path!='runtime/feedback.ts'));self.assertIs(evaluate(sample_document(),b).status,GateStatus.FAIL)
 def test_no_blocking_findings(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='blocking_feedback_findings'),0)
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
 def test_product_not_accepted(self):self.assertFalse(self.good().product_accepted)
