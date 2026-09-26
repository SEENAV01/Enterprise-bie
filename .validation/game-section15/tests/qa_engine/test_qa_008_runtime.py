import unittest
from dataclasses import replace
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_008 import evaluate
class Tests(unittest.TestCase):
 def good(self):return evaluate(runtime_result())
 def test_pass(self):assert_pass(self,self.good())
 def test_all_components_verified(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='runtime_evidence_components'),6)
 def test_no_external_requests(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='external_requests'),0)
 def test_no_runtime_errors(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='runtime_errors'),0)
 def test_replay_nondeterminism_fails(self):
  rr=runtime_result();bad=replace(rr,replay=replace(rr.replay,identical_second_run=False));self.assertIs(evaluate(bad).status,GateStatus.FAIL)
 def test_browser_external_request_fails(self):
  rr=runtime_result();bad=replace(rr,browser=replace(rr.browser,external_requests=('https://example.com',)));self.assertIs(evaluate(bad).status,GateStatus.FAIL)
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
