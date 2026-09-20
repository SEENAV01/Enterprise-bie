from hashlib import sha256
from bie.animation_intelligence.temporal_contracts import *
def C(**kw):
 d=dict(intent_id="time",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),source_revision=1)
 d.update(kw);return Context(**d)
def E(i,order=None,time=None,uncertain=False,group=None,src="src"):return Event(i,i,src,order,time,uncertain,group)

import unittest
from bie.animation_intelligence.timeline_animation import *
class T(unittest.TestCase):
 def test_ordinal(self):self.assertEqual(animate_timeline(C(),"t",[E("a",0),E("b",1)]).status,"PASS")
 def test_missing_order(self):self.assertEqual(animate_timeline(C(),"t",[E("a"),E("b",1)]).status,"BLOCKED")
 def test_prop(self):self.assertEqual(animate_timeline(C(),"t",[E("a",time=1900),E("b",time=1950)],"proportional").status,"PASS")
 def test_prop_missing(self):self.assertEqual(animate_timeline(C(),"t",[E("a",time=1900),E("b")],"proportional").status,"BLOCKED")
 def test_uncertain_review(self):self.assertEqual(animate_timeline(C(),"t",[E("a",0,uncertain=True),E("b",1)]).status,"REVIEW")
 def test_uncertain_block(self):self.assertEqual(animate_timeline(C(),"t",[E("a",0,uncertain=True),E("b",1)],preserve_uncertainty=False).status,"BLOCKED")
 def test_ground(self):
  with self.assertRaises(TimeGroundingError):animate_timeline(C(),"t",[E("a",0,src="x"),E("b",1)])
 def test_accept(self):self.assertFalse(animate_timeline(C(),"t",[E("a",0),E("b",1)]).accepted)
