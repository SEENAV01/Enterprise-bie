import unittest
from dataclasses import replace
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_001 import evaluate
class Tests(unittest.TestCase):
 def good(self):
  b=rich_bundle();return evaluate(b.objectives,all_strategy_plans(),b.provenance)
 def test_pass(self):assert_pass(self,self.good())
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
 def test_all_metrics_full(self):self.assertTrue(all(m.value>=1 for m in self.good().metrics[:3]))
 def test_missing_plan_fails(self):
  b=rich_bundle();r=evaluate(b.objectives,all_strategy_plans()[:-1],b.provenance);self.assertIs(r.status,GateStatus.FAIL)
 def test_missing_plan_has_objective_finding(self):self.assertTrue(any(f.code=='OBJECTIVES_MISSING' for f in evaluate(rich_bundle().objectives,all_strategy_plans()[:-1],rich_bundle().provenance).findings))
 def test_strict_policy(self):assert_pass(self,evaluate(rich_bundle().objectives,all_strategy_plans(),rich_bundle().provenance,GameQAPolicy()))
 def test_strategy_diversity(self):self.assertGreaterEqual(next(m.value for m in self.good().metrics if m.name=='strategy_diversity'),9)
 def test_product_not_accepted(self):self.assertFalse(self.good().product_accepted)
