from hashlib import sha256
from bie.animation_intelligence.physics_contracts import *
def C(**kw):
 d=dict(intent_id="p",evidence_refs=("src",),reasoning_refs=("r",),visual_plan_fingerprint=sha256(b"vis").hexdigest(),frame="xy")
 d.update(kw);return Context(**d)

import unittest
from bie.animation_intelligence.physics_animation_semantics import build
from bie.animation_intelligence.vector_animation import animate as avec
from bie.animation_intelligence.field_line_animation import animate as afield
from bie.animation_intelligence.physics_graph_animation import animate as agraph
from bie.animation_intelligence.particle_animation import animate as apart
class T(unittest.TestCase):
 def test_force_vector(self):
  self.assertEqual((build(C(),"force").status,avec(C(),"F",(3,4),"N",(0,0),"src",5).status),("PASS","PASS"))
 def test_field_review(self):self.assertEqual(afield(C(),"E",[[(0,0),(1,0)]],"src").status,"REVIEW")
 def test_graph_block(self):self.assertEqual(agraph(C(),"g",[(0,0),(1,1)],"src","t","s","x","m",True,True).status,"BLOCKED")
 def test_particle_review(self):self.assertEqual(apart(C(),"s",[{"particle_id":"1","trajectory":[(0,0),(1,0)]}],"src",4).status,"REVIEW")
 def test_not_accepted(self):self.assertFalse(avec(C(),"F",(1,0),"N",(0,0),"src").accepted)
