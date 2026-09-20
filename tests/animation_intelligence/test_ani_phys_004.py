from hashlib import sha256
from bie.animation_intelligence.physics_contracts import *
def C(**kw):
 d=dict(intent_id="p",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),frame="xy")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.physics_graph_animation import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(animate(C(),"g",[(0,0),(1,2)],"src","t","s","x","m").status,"PASS")
 def test_sample_exact(self):self.assertEqual(animate(C(),"g",[(0,0),(1,2)],"src","t","s","x","m",True,True).status,"BLOCKED")
 def test_domain(self):self.assertEqual(animate(C(),"g",[(0,0),(1,2)],"src","t","s","x","m",domain=(0,1)).status,"PASS")
 def test_domain_block(self):self.assertEqual(animate(C(),"g",[(0,0),(2,2)],"src","t","s","x","m",domain=(0,1)).status,"BLOCKED")
 def test_source(self):
  with self.assertRaises(GroundingError):animate(C(),"g",[(0,0),(1,2)],"x","t","s","x","m")
 def test_accept(self):self.assertFalse(animate(C(),"g",[(0,0),(1,2)],"src","t","s","x","m").accepted)
