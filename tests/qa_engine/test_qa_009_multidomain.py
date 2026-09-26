import unittest
from dataclasses import replace
from bie.game_engine.qa_engine.qa_009 import evaluate
from bie.game_engine.qa_engine.contracts import GateStatus
from tests.hardening_h2.support import benchmarks
from tests.qa_engine.support import assert_pass
class Tests(unittest.TestCase):
 def good(self):return evaluate(benchmarks())
 def test_pass(self):assert_pass(self,self.good())
 def test_eight_domains(self):self.assertEqual(len(benchmarks()),8)
 def test_strategy_diversity(self):self.assertGreaterEqual(next(m.value for m in self.good().metrics if m.name=='strategy_kinds'),7)
 def test_zero_clone_ratio(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='clone_ratio'),0)
 def test_too_few_domains_fails(self):self.assertIs(evaluate(benchmarks()[:2]).status,GateStatus.FAIL)
 def test_wrong_expected_mechanic_fails_closed_at_evidence_validation(self):
  rows=list(benchmarks());rows[0]=replace(rows[0],expected_mechanic='retrieval')
  with self.assertRaises(Exception):evaluate(tuple(rows))
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
