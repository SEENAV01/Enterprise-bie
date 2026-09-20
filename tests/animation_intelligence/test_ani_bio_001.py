from hashlib import sha256
from bie.animation_intelligence.biology_contracts import *
def C(**kw):
 d=dict(intent_id="bio",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),scale_level="cellular")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.process_animation import *
S=({"state_id":"a"},{"state_id":"b"});T=({"transition_id":"t","from":"a","to":"b"},)
class X(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate_process(C(),"p","transport",S,T,"src").status,"PASS")
 def test_unknown(self):self.assertEqual(animate_process(C(),"p","unknown",S,T,"src").status,"UNSUPPORTED")
 def test_direction(self):self.assertEqual(animate_process(C(),"p","transport",S,T,"src",False).status,"BLOCKED")
 def test_bad_transition(self):
  with self.assertRaises(BioTopologyError):animate_process(C(),"p","transport",S,({"transition_id":"x","from":"a","to":"z"},),"src")
 def test_causal_review(self):self.assertEqual(animate_process(C(),"p","signaling",S,T,"src",causal_claims=True).status,"REVIEW")
 def test_bound_model(self):self.assertEqual(animate_process(C(model_fingerprint=sha256(b"m").hexdigest()),"p","signaling",S,T,"src",causal_claims=True).status,"PASS")
 def test_cyclic_review(self):self.assertEqual(animate_process(C(),"p","cell_cycle",S,T,"src",cyclic=True).status,"REVIEW")
 def test_accept(self):self.assertFalse(animate_process(C(),"p","transport",S,T,"src").accepted)
