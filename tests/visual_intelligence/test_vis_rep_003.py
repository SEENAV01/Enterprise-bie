import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep003_diagram_sim import *
def I(**kw):
 d=dict(intent_id='i',domain='physics',concept_ids=('c',),evidence_refs=('e',),reasoning_refs=('r',),semantic_tags=('process',));d.update(kw);return SemanticIntent(**d)
def P(**kw):
 d=dict(profile_id='web',capabilities=('2d',),supports_simulation=False);d.update(kw);return TargetProfile(**d)
class T(unittest.TestCase):
 def test_static(self):self.assertEqual(choose(I(),P()).selected,'diagram')
 def test_dynamic(self):self.assertEqual(choose(I(dynamic=True),P(supports_simulation=True),True,4,True).selected,'simulation')
 def test_nomodel(self):self.assertEqual(choose(I(dynamic=True),P(supports_simulation=True),True,4,False).status,'REVIEW')
 def test_fallback(self):self.assertEqual(choose(I(dynamic=True),P(),True,4,True).selected,'diagram')
 def test_bad(self):
  with self.assertRaises(RepresentationError):choose(I(),P(),mechanism_states=0)
 def test_ground(self):self.assertEqual(choose(I(),P()).evidence_refs,('e',))
 def test_accept(self):self.assertFalse(choose(I(),P()).accepted)
 def test_det(self):self.assertEqual(choose(I(),P()).fingerprint,choose(I(),P()).fingerprint)
def add(n,d,e,s,m,sup,exp):
 def t(self):self.assertEqual(choose(I(dynamic=d),P(supports_simulation=sup),e,s,m).selected,exp)
 setattr(T,f'test_case_{n}',t)
for i,c in enumerate([(False,False,1,False,False,'diagram'),(True,False,1,True,True,'diagram'),(True,True,3,True,True,'simulation'),(True,True,5,True,False,'diagram'),(True,False,5,True,True,'simulation'),(False,True,4,True,True,'diagram'),(False,False,4,False,True,'diagram'),(True,True,2,True,True,'simulation'),(True,False,2,False,True,'diagram'),(False,True,2,False,True,'diagram')]):add(i,*c)
