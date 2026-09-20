from hashlib import sha256
from bie.animation_intelligence.physics_contracts import *
def C(**kw):
 d=dict(intent_id="p",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),frame="xy")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.vector_animation import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate(C(),"F",(3,4),"N",(0,0),"src").status,"PASS")
 def test_mag(self):self.assertAlmostEqual(animate(C(),"F",(3,4),"N",(0,0),"src").ops[0]["magnitude"],5)
 def test_conflict(self):self.assertEqual(animate(C(),"F",(3,4),"N",(0,0),"src",6).status,"BLOCKED")
 def test_transform(self):self.assertEqual(len(animate(C(),"F",(1,0),"N",(0,0),"src",target_components=(0,1)).ops),2)
 def test_source(self):
  with self.assertRaises(GroundingError):animate(C(),"F",(1,0),"N",(0,0),"x")
 def test_accept(self):self.assertFalse(animate(C(),"F",(1,0),"N",(0,0),"src").accepted)
