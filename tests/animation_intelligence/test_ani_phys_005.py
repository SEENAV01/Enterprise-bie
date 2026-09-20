from hashlib import sha256
from bie.animation_intelligence.physics_contracts import *
def C(**kw):
 d=dict(intent_id="p",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),frame="xy")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.particle_animation import *
P=[{"particle_id":"p","trajectory":[(0,0),(1,0)]}]
class T(unittest.TestCase):
 def test_review(self):self.assertEqual(animate(C(),"sys",P,"src",1).status,"REVIEW")
 def test_observed(self):self.assertEqual(animate(C(),"sys",P,"src",1,observed_execution=True).status,"PASS")
 def test_illustrative(self):self.assertEqual(animate(C(),"sys",P,"src",1,"illustrative").status,"REVIEW")
 def test_model_block(self):self.assertEqual(animate(C(),"sys",P,"src",1,"model_output").status,"BLOCKED")
 def test_model_review(self):self.assertEqual(animate(C(model_fingerprint=sha256(b"m").hexdigest()),"sys",P,"src",1,"model_output").status,"REVIEW")
 def test_accept(self):self.assertFalse(animate(C(),"sys",P,"src",1).accepted)
