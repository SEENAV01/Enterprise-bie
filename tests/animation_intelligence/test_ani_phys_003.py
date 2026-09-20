from hashlib import sha256
from bie.animation_intelligence.physics_contracts import *
def C(**kw):
 d=dict(intent_id="p",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),frame="xy")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.field_line_animation import *
class T(unittest.TestCase):
 def test_review(self):self.assertEqual(animate(C(),"E",[[(0,0),(1,0)]],"src").status,"REVIEW")
 def test_pass_encoding(self):self.assertEqual(animate(C(),"E",[[(0,0),(1,0)]],"src",magnitude_encoding="width").status,"PASS")
 def test_direction(self):self.assertEqual(animate(C(),"E",[[(0,0),(1,0)]],"src",False).status,"BLOCKED")
 def test_model_block(self):self.assertEqual(animate(C(),"E",[[(0,0),(1,0)]],"src",generated_from_model=True).status,"BLOCKED")
 def test_model_pass(self):self.assertNotEqual(animate(C(model_fingerprint=sha256(b"m").hexdigest()),"E",[[(0,0),(1,0)]],"src",generated_from_model=True).status,"BLOCKED")
 def test_accept(self):self.assertFalse(animate(C(),"E",[[(0,0),(1,0)]],"src").accepted)
