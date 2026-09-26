import unittest
from bie.game_engine.state_engine.reachability import StateNode,StateEdge,TransitionSystem
from tests.qa_engine.support import *
from bie.game_engine.qa_engine.qa_003 import evaluate
class Tests(unittest.TestCase):
 def good(self):return evaluate(healthy_transition_system(),'s0',{'c':'s2'})
 def test_pass(self):assert_pass(self,self.good())
 def test_path_metric(self):self.assertEqual(next(m.value for m in self.good().metrics if m.name=='challenge_reachability'),1)
 def test_unreachable_fails(self):
  s=TransitionSystem((StateNode('a','sha256:'+'0'*64),StateNode('b','sha256:'+'1'*64,True)),(),10,False);self.assertIs(evaluate(s,'a',{'c':'b'}).status,GateStatus.FAIL)
 def test_multiple_challenge_targets(self):self.assertIs(evaluate(healthy_transition_system(),'s0',{'c1':'s1','c2':'s2'}).status,GateStatus.PASS)
 def test_empty_targets_rejected(self):
  with self.assertRaises(ValueError):evaluate(healthy_transition_system(),'s0',{})
 def test_deterministic(self):self.assertEqual(self.good(),self.good())
 def test_product_not_accepted(self):self.assertFalse(self.good().product_accepted)
