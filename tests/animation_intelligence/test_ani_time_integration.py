from hashlib import sha256
from bie.animation_intelligence.temporal_contracts import *
def C(**kw):
 d=dict(intent_id="time",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),source_revision=1)
 d.update(kw);return Context(**d)
def E(i,order=None,time=None,uncertain=False,group=None,src="src"):return Event(i,i,src,order,time,uncertain,group)

import unittest
from bie.animation_intelligence.timeline_animation import animate_timeline
from bie.animation_intelligence.chronology_reveal import animate_chronology
class T(unittest.TestCase):
 def test_pipeline(self):
  ev=[E("a",0),E("b",1),E("c",2)]
  self.assertEqual((animate_timeline(C(),"t",ev).status,animate_chronology(C(),"c",ev,[{"before":"a","after":"b"},{"before":"b","after":"c"}]).status),("PASS","PASS"))
 def test_uncertainty_guard(self):self.assertEqual(animate_timeline(C(),"t",[E("a",0,uncertain=True),E("b",1)],preserve_uncertainty=False).status,"BLOCKED")
 def test_cycle_guard(self):self.assertEqual(animate_chronology(C(),"c",[E("a",0),E("b",1)],[{"before":"a","after":"b"},{"before":"b","after":"a"}]).status,"BLOCKED")
 def test_not_accepted(self):self.assertFalse(animate_timeline(C(),"t",[E("a",0),E("b",1)]).accepted)
