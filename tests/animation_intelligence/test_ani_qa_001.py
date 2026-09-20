from bie.animation_intelligence.qa_contracts import *
def E(i,action="reveal",targets=("v",),s=0,en=500,purpose="introduce",rev=2,pri=.8,motion=.3,essential=True):
 return Event(i,action,targets,s,en,purpose,("src",),("r",),rev,pri,motion,essential)

import unittest
from bie.animation_intelligence.temporal_conflict_qa import evaluate
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(evaluate([E("a",s=0,en=100),E("b",targets=("x",),s=100,en=200)]).status,"PASS")
 def test_overlap(self):self.assertEqual(evaluate([E("a",s=0,en=150),E("b",s=100,en=200)]).status,"BLOCKED")
 def test_allow(self):self.assertNotEqual(evaluate([E("a",s=0,en=150),E("b",s=100,en=200)],True).status,"BLOCKED")
 def test_rate(self):self.assertEqual(evaluate([E("a","trace",("a",),0,200,"show_direction"),E("b","path_follow",("b",),50,250,"show_direction")]).status,"REVIEW")
 def test_concurrency(self):self.assertEqual(evaluate([E("a",targets=("a",),s=0,en=300),E("b",targets=("b",),s=0,en=300),E("c",targets=("c",),s=0,en=300)]).status,"BLOCKED")
 def test_empty(self):self.assertEqual(evaluate([]).status,"UNSUPPORTED")
 def test_score(self):self.assertIsNotNone(evaluate([E("a")]).score)
 def test_accept(self):self.assertFalse(evaluate([E("a")]).accepted)
