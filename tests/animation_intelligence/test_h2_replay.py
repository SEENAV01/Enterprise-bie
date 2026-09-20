import unittest
from bie.animation_intelligence.ani_replay_currentness import *
def V(v=1):return VersionVector(v,1,1,"1.0","web")
class T(unittest.TestCase):
 def test_current(self):
  r=make_replay_record("x",V(),"in","out",("d",));self.assertTrue(assert_current(r,V(),"in",("d",)))
 def test_stale_revision(self):
  r=make_replay_record("x",V(),"in","out",("d",))
  with self.assertRaises(ReplayCurrentnessError):assert_current(r,V(2),"in",("d",))
 def test_stale_input(self):
  r=make_replay_record("x",V(),"in","out",("d",))
  with self.assertRaises(ReplayCurrentnessError):assert_current(r,V(),"in2",("d",))
 def test_invalidate(self):
  r=invalidate(make_replay_record("x",V(),"in","out",("d",)),"vis_changed")
  with self.assertRaises(ReplayCurrentnessError):assert_current(r,V(),"in",("d",))
 def test_match(self):
  a=make_replay_record("a",V(),"in","out",("d",));b=make_replay_record("b",V(),"in","out",("d",));self.assertTrue(replay_matches(a,b))
 def test_dep(self):
  r=make_replay_record("x",V(),"in","out",("d",))
  with self.assertRaises(ReplayCurrentnessError):assert_current(r,V(),"in",("e",))
 def test_not_accepted(self):self.assertFalse(make_replay_record("x",V(),"in","out",("d",)).accepted)
