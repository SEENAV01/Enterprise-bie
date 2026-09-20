from hashlib import sha256
from bie.animation_intelligence.physics_contracts import *
def C(**kw):
 d=dict(intent_id="p",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),frame="xy")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.physics_animation_semantics import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(build(C(),"force").status,"PASS")
 def test_unknown(self):self.assertEqual(build(C(),"astrology").status,"UNSUPPORTED")
 def test_causal_review(self):self.assertEqual(build(C(),"force",["force changes momentum"]).status,"REVIEW")
 def test_bound_model(self):self.assertEqual(build(C(model_fingerprint=sha256(b"m").hexdigest()),"force",["force changes momentum"]).status,"PASS")
 def test_uncertain(self):self.assertEqual(build(C(uncertainty=.5),"wave").status,"REVIEW")
 def test_accept(self):self.assertFalse(build(C(),"force").accepted)
