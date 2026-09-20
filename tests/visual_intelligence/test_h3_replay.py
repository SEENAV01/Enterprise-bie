import unittest
from bie.visual_intelligence.replay_currentness import *
class T(unittest.TestCase):
 def v(self): return VersionVector(1,2,'1.0.0','1.0.0','web')
 def test_current(self):
  r=make_replay_record('run',self.v(),'in','out',('a','b'));self.assertTrue(assert_current(r,self.v(),'in',('b','a')))
 def test_vector_change(self):
  r=make_replay_record('run',self.v(),'in','out',('a',))
  with self.assertRaises(StaleArtifactError): assert_current(r,VersionVector(2,2,'1.0.0','1.0.0','web'),'in',('a',))
 def test_dep_change(self):
  r=make_replay_record('run',self.v(),'in','out',('a',))
  with self.assertRaises(StaleArtifactError): assert_current(r,self.v(),'in',('a','b'))
 def test_invalidate(self): self.assertFalse(invalidate(make_replay_record('run',self.v(),'in','out',('a',)),'source change').current)
 def test_match(self): self.assertTrue(replay_matches(make_replay_record('run',self.v(),'in','out',('a',)),'out'))
