from bie.animation_intelligence.qa_contracts import *
def E(i,action="reveal",targets=("v",),s=0,en=500,purpose="introduce",rev=2,pri=.8,motion=.3,essential=True):
 return Event(i,action,targets,s,en,purpose,("src",),("r",),rev,pri,motion,essential)

import unittest
from bie.animation_intelligence.excessive_motion_qa import evaluate
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(evaluate([E("a",motion=.2)]).status,"PASS")
 def test_budget(self):self.assertEqual(evaluate([E("a","camera",("a",),motion=1),E("b","morph",("b",),motion=1),E("c","trace",("c",),motion=1)]).status,"BLOCKED")
 def test_reduced(self):self.assertEqual(evaluate([E("a","camera",motion=.8)],True).status,"BLOCKED")
 def test_decorative(self):self.assertEqual(evaluate([E("a",motion=.8,essential=False)]).status,"REVIEW")
 def test_high(self):self.assertEqual(evaluate([E(str(i),"camera",(str(i),),motion=.8) for i in range(4)],max_budget=100).status,"BLOCKED")
 def test_payload(self):self.assertGreater(evaluate([E("a",motion=.2)]).payload["budget"],0)
 def test_score(self):self.assertIsNotNone(evaluate([E("a")]).score)
 def test_accept(self):self.assertFalse(evaluate([E("a")]).accepted)
