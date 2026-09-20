from bie.animation_intelligence.qa_contracts import *
def E(i,action="reveal",targets=("v",),s=0,en=500,purpose="introduce",rev=2,pri=.8,motion=.3,essential=True):
 return Event(i,action,targets,s,en,purpose,("src",),("r",),rev,pri,motion,essential)

import unittest
from bie.animation_intelligence.animation_synchronization_qa import evaluate
C=[{"cue_id":"c","start_ms":0,"end_ms":1000}]
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(evaluate([E("a",s=0,en=1000)],2,C).status,"PASS")
 def test_stale(self):self.assertEqual(evaluate([E("a",s=0,en=1000,rev=1)],2,C).status,"BLOCKED")
 def test_unbound(self):self.assertEqual(evaluate([E("a",s=1200,en=1500)],2,C).status,"BLOCKED")
 def test_drift(self):self.assertEqual(evaluate([E("a",s=300,en=900)],2,C).status,"REVIEW")
 def test_escape(self):self.assertEqual(evaluate([E("a",s=900,en=1200)],2,C).status,"BLOCKED")
 def test_notrun(self):self.assertEqual(evaluate([],2,C).status,"NOT_RUN")
 def test_payload(self):self.assertEqual(evaluate([E("a",s=0,en=1000)],2,C).payload["pairs"][0]["cue_id"],"c")
 def test_accept(self):self.assertFalse(evaluate([E("a",s=0,en=1000)],2,C).accepted)
