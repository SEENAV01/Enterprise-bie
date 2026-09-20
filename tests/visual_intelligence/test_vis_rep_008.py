import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep008_dimension import *
def I(**kw):
 d=dict(intent_id='i',domain='biology',concept_ids=('c',),evidence_refs=('e',),reasoning_refs=('r',),semantic_tags=('structure',));d.update(kw);return SemanticIntent(**d)
def P(**kw):
 d=dict(profile_id='web',capabilities=('2d',),supports_3d=False,max_complexity=.8);d.update(kw);return TargetProfile(**d)
class T(unittest.TestCase):
 def test_2d(self):self.assertEqual(dimension(I(),P()).selected,'2d')
 def test_3d(self):self.assertEqual(dimension(I(),P(supports_3d=True),depth_semantics=True,volumetric_structure=True).selected,'3d')
 def test_required(self):self.assertEqual(dimension(I(),P(),three_d_required=True).status,'BLOCKED')
 def test_complex(self):self.assertEqual(dimension(I(),P(supports_3d=True,max_complexity=.4),depth_semantics=True,volumetric_structure=True,estimated_complexity=.9).selected,'2d')
 def test_occlusion(self):self.assertEqual(dimension(I(),P(supports_3d=True),depth_semantics=True,occlusion_semantics=True).selected,'3d')
 def test_camera(self):self.assertEqual(dimension(I(),P(supports_3d=True),camera_motion_value=1).selected,'2d')
 def test_bad(self):
  with self.assertRaises(RepresentationError):dimension(I(),P(),estimated_complexity=2)
 def test_ground(self):self.assertEqual(dimension(I(),P()).reasoning_refs,('r',))
 def test_accept(self):self.assertFalse(dimension(I(),P()).accepted)
 def test_primary(self):self.assertEqual(compose(I(),[('diagram',.9),('equation',.7)],dimension(I(),P())).primary,'diagram')
 def test_second(self):self.assertEqual(compose(I(),[('diagram',.9),('equation',.7),('graph',.65)],dimension(I(),P())).secondary,('equation','graph'))
 def test_trim(self):self.assertEqual(len(compose(I(),[('diagram',.9),('equation',.8),('graph',.7)],dimension(I(),P()),complexity=.9).secondary),1)
 def test_blocked(self):self.assertEqual(compose(I(),[('3d_model',.95),('diagram',.7)],dimension(I(),P(),three_d_required=True)).status,'BLOCKED')
 def test_empty(self):
  with self.assertRaises(RepresentationError):compose(I(),[],dimension(I(),P()))
 def test_plan_accept(self):self.assertFalse(compose(I(),[('diagram',.9)],dimension(I(),P())).accepted)
def add(n,d,o,v,s,c,exp):
 def t(self):self.assertEqual(dimension(I(),P(supports_3d=s),depth_semantics=d,occlusion_semantics=o,volumetric_structure=v,estimated_complexity=c).selected,exp)
 setattr(T,f'test_case_{n}',t)
for i,c in enumerate([(False,False,False,False,.2,'2d'),(True,False,False,False,.2,'2d'),(True,True,False,True,.2,'3d'),(True,False,True,True,.2,'3d'),(False,True,True,True,.2,'2d'),(True,True,True,True,.2,'3d'),(True,True,True,False,.2,'2d'),(True,True,True,True,.9,'2d'),(False,False,True,True,.2,'2d'),(True,False,True,False,.2,'2d'),(False,True,False,True,.2,'2d'),(True,True,False,False,.2,'2d'),(True,False,False,True,.2,'2d'),(False,False,False,True,.2,'2d'),(True,True,True,True,.7,'3d'),(True,False,True,True,.7,'3d'),(True,True,False,True,.7,'3d'),(False,True,True,True,.7,'2d'),(False,False,True,False,.2,'2d'),(False,True,False,False,.2,'2d')]):add(i,*c)
