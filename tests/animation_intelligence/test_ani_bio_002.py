from hashlib import sha256
from bie.animation_intelligence.biology_contracts import *
def C(**kw):
 d=dict(intent_id="bio",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),scale_level="cellular")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.molecular_cellular_flow import *
COMP=({"compartment_id":"out","kind":"extracellular_space"},{"compartment_id":"mem","kind":"membrane"},{"compartment_id":"in","kind":"cell"})
TR=({"transfer_id":"t","from":"out","to":"in","molecule":"glucose","amount":1.0,"unit":"mol"},)
class X(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate_flow(C(),"f",COMP,TR,"src").status,"PASS")
 def test_direction(self):self.assertEqual(animate_flow(C(),"f",COMP,TR,"src",False).status,"BLOCKED")
 def test_bad_topology(self):
  with self.assertRaises(BioTopologyError):animate_flow(C(),"f",COMP,({"transfer_id":"x","from":"out","to":"z","molecule":"x"},),"src")
 def test_model_block(self):self.assertEqual(animate_flow(C(),"f",COMP,TR,"src",model_generated=True).status,"BLOCKED")
 def test_model_pass(self):self.assertEqual(animate_flow(C(model_fingerprint=sha256(b"m").hexdigest()),"f",COMP,TR,"src",model_generated=True).status,"PASS")
 def test_concentration_review(self):
  tr=({"transfer_id":"t","from":"out","to":"in","molecule":"glucose"},)
  self.assertEqual(animate_flow(C(),"f",COMP,tr,"src",concentration_claims=True).status,"REVIEW")
 def test_permeability_review(self):
  c=({"compartment_id":"a","kind":"cell"},{"compartment_id":"b","kind":"cell"})
  tr=({"transfer_id":"t","from":"a","to":"b","molecule":"x"},)
  self.assertEqual(animate_flow(C(),"f",c,tr,"src",permeability_claims=True).status,"REVIEW")
 def test_accept(self):self.assertFalse(animate_flow(C(),"f",COMP,TR,"src").accepted)
