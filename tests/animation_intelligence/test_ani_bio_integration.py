from hashlib import sha256
from bie.animation_intelligence.biology_contracts import *
def C(**kw):
 d=dict(intent_id="bio",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),scale_level="cellular")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.process_animation import animate_process
from bie.animation_intelligence.molecular_cellular_flow import animate_flow
class T(unittest.TestCase):
 def test_transport_flow(self):
  p=animate_process(C(),"transport","transport",({"state_id":"out"},{"state_id":"in"}),({"transition_id":"t","from":"out","to":"in"},),"src")
  f=animate_flow(C(),"flow",({"compartment_id":"out","kind":"extracellular_space"},{"compartment_id":"in","kind":"cell"}),({"transfer_id":"t","from":"out","to":"in","molecule":"glucose"},),"src")
  self.assertEqual((p.status,f.status),("PASS","PASS"))
 def test_truth_boundary(self):
  p=animate_process(C(),"sig","signaling",({"state_id":"off"},{"state_id":"on"}),({"transition_id":"t","from":"off","to":"on"},),"src",causal_claims=True)
  self.assertEqual(p.status,"REVIEW")
 def test_topology_guard(self):
  with self.assertRaises(BioTopologyError):animate_flow(C(),"x",({"compartment_id":"a","kind":"cell"},{"compartment_id":"b","kind":"cell"}),({"transfer_id":"t","from":"a","to":"z","molecule":"x"},),"src")
 def test_not_accepted(self):
  self.assertFalse(animate_process(C(),"p","transport",({"state_id":"a"},{"state_id":"b"}),({"transition_id":"t","from":"a","to":"b"},),"src").accepted)
