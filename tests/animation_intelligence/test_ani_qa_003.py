from bie.animation_intelligence.qa_contracts import *
def E(i,action="reveal",targets=("v",),s=0,en=500,purpose="introduce",rev=2,pri=.8,motion=.3,essential=True):
 return Event(i,action,targets,s,en,purpose,("src",),("r",),rev,pri,motion,essential)

import unittest
from bie.animation_intelligence.animation_purpose_alignment_qa import evaluate
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(evaluate([E("a","reveal",purpose="introduce")]).status,"PASS")
 def test_misaligned(self):self.assertEqual(evaluate([E("a","exit",purpose="introduce")]).status,"BLOCKED")
 def test_unmapped(self):self.assertEqual(evaluate([E("a",purpose="decorate")]).status,"BLOCKED")
 def test_unmapped_review(self):self.assertEqual(evaluate([E("a",purpose="decorate")],True).status,"REVIEW")
 def test_nonessential(self):self.assertEqual(evaluate([E("a","emphasize",purpose="focus",essential=False)]).status,"REVIEW")
 def test_relation(self):self.assertEqual(evaluate([E("a","trace",purpose="show_relation")]).status,"PASS")
 def test_score(self):self.assertGreater(evaluate([E("a")]).score,.9)
 def test_accept(self):self.assertFalse(evaluate([E("a")]).accepted)
