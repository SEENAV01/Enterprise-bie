import unittest
from bie.game_engine.state_engine.reachability import StateNode,StateEdge,TransitionSystem
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_004 import evaluate
class Tests(unittest.TestCase):
 def good(self):return evaluate(healthy_transition_system(),'s0',('s2',))
 def test_pass(self):assert_pass(self,self.good())
 def test_dead_end_fails(self):self.assertIs(evaluate(dead_end_transition_system(),'s0',('goal',)).status,GateStatus.FAIL)
 def test_dead_end_finding(self):self.assertTrue(any(f.code=='NONTERMINAL_DEAD_END' for f in evaluate(dead_end_transition_system(),'s0',('goal',)).findings))
 def test_unreachable_state_fails(self):
  s=TransitionSystem((StateNode('a','sha256:'+'0'*64),StateNode('g','sha256:'+'1'*64,True),StateNode('u','sha256:'+'2'*64)),(StateEdge('e','a','g','t'),),10,False);self.assertIs(evaluate(s,'a',('g',)).status,GateStatus.FAIL)
 def test_metrics_zero(self):self.assertTrue(all(m.value==0 for m in self.good().metrics))
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
 def test_product_not_accepted(self):self.assertFalse(self.good().product_accepted)
