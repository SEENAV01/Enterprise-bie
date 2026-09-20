import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep002_fitness import *
def I():return SemanticIntent('i','physics',('c',),('e',),('r',),('vector',))
def C(caps=()):return Candidate('x','diagram',('e',),('r',),caps,('why',),.9)
def P(**kw):
 d=dict(profile_id='web',capabilities=('2d','math_text'),supports_3d=False,supports_simulation=False);d.update(kw);return TargetProfile(**d)
def S(c=None,p=None):return score(I(),c or C(),p or P(),.9,.8,.8,.9,.9)
class T(unittest.TestCase):
 def test_good(self):self.assertGreater(S().total,.8)
 def test_3d(self):self.assertIn('target_lacks_3d',S(C(('3d',))).blockers)
 def test_sim(self):self.assertIn('target_lacks_simulation',S(C(('simulation',))).blockers)
 def test_2d(self):self.assertEqual(S(C(('2d',))).capability_fit,1)
 def test_missing(self):self.assertTrue(S(C(('special',))).blockers)
 def test_det(self):self.assertEqual(S().fingerprint,S().fingerprint)
 def test_keys(self):
  with self.assertRaises(RepresentationError):score(I(),C(),P(),.9,.8,.8,.9,.9,{'x':1})
 def test_sum(self):
  w=dict(W);w['semantic_fidelity']=.5
  with self.assertRaises(RepresentationError):score(I(),C(),P(),.9,.8,.8,.9,.9,w)
 def test_bound(self):self.assertLessEqual(S().total,1)
 def test_blockcap(self):self.assertLessEqual(S(C(('3d',))).total,.49)
