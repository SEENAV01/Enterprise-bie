from hashlib import sha256
from bie.animation_intelligence.temporal_contracts import *
def C(**kw):
 d=dict(intent_id="time",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),source_revision=1)
 d.update(kw);return Context(**d)
def E(i,order=None,time=None,uncertain=False,group=None,src="src"):return Event(i,i,src,order,time,uncertain,group)

import unittest
from bie.animation_intelligence.chronology_reveal import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate_chronology(C(),"c",[E("a",0),E("b",1)]).status,"PASS")
 def test_dep(self):self.assertEqual(animate_chronology(C(),"c",[E("a",1),E("b",0)],[{"before":"a","after":"b"}]).ops[0]["event_order"][0],"a")
 def test_cycle(self):self.assertEqual(animate_chronology(C(),"c",[E("a",0),E("b",1)],[{"before":"a","after":"b"},{"before":"b","after":"a"}]).status,"BLOCKED")
 def test_simultaneous(self):self.assertEqual(animate_chronology(C(),"c",[E("a",0,group="g"),E("b",0,group="g")]).status,"PASS")
 def test_sim_block(self):self.assertEqual(animate_chronology(C(),"c",[E("a",0,group="g"),E("b",0,group="g")],allow_simultaneous=False).status,"BLOCKED")
 def test_uncertain(self):self.assertEqual(animate_chronology(C(),"c",[E("a",0,uncertain=True),E("b",1)]).status,"REVIEW")
 def test_exact_block(self):self.assertEqual(animate_chronology(C(),"c",[E("a",0,uncertain=True),E("b",1)],exact_date_claims=True).status,"BLOCKED")
 def test_accept(self):self.assertFalse(animate_chronology(C(),"c",[E("a",0),E("b",1)]).accepted)
