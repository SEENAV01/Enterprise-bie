from bie.animation_intelligence.qa_contracts import *
def E(i,action="reveal",targets=("v",),s=0,en=500,purpose="introduce",rev=2,pri=.8,motion=.3,essential=True):
 return Event(i,action,targets,s,en,purpose,("src",),("r",),rev,pri,motion,essential)

import unittest
from bie.animation_intelligence.temporal_conflict_qa import evaluate as temporal
from bie.animation_intelligence.excessive_motion_qa import evaluate as motion
from bie.animation_intelligence.animation_purpose_alignment_qa import evaluate as purpose
from bie.animation_intelligence.animation_synchronization_qa import evaluate as sync
from bie.animation_intelligence.animation_benchmark import Case,run
class T(unittest.TestCase):
 def test_clean_pipeline(self):
  es=[E("a","reveal",("v",),0,1000,"introduce",motion=.2)]
  self.assertEqual((temporal(es).status,motion(es).status,purpose(es).status,sync(es,2,[{"cue_id":"c","start_ms":0,"end_ms":1000}]).status),("PASS","PASS","PASS","PASS"))
 def test_conflict(self):self.assertEqual(temporal([E("a",targets=("v",),s=0,en=600),E("b",targets=("v",),s=100,en=700)]).status,"BLOCKED")
 def test_benchmark(self):self.assertEqual(run([Case("c",.95,.95,.95,.95,.95,True)]).status,"PASS")
 def test_empirical_boundary(self):self.assertEqual(run([Case("c",.95,.95,.95,.95,.95,None)],require_empirical=True).status,"BLOCKED")
 def test_not_accepted(self):self.assertFalse(purpose([E("a")]).accepted)
