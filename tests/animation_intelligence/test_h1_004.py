import unittest
from bie.animation_intelligence.global_timeline_solver import *
class T(unittest.TestCase):
 def test_pass(self):self.assertTrue(solve([TrackRequest("a",0,100,0,500)]).solved)
 def test_shift(self):self.assertTrue(solve([TrackRequest("a",0,100,0,500,.9,"g"),TrackRequest("b",50,100,0,500,.5,"g")]).solved)
 def test_unsat(self):self.assertFalse(solve([TrackRequest("a",0,400,0,500,.9,"g"),TrackRequest("b",100,400,0,500,.5,"g")]).solved)
 def test_dup(self):
  with self.assertRaises(TimelineSolveError):solve([TrackRequest("a",0,10,0,100),TrackRequest("a",20,10,0,100)])
 def test_sorted(self):self.assertEqual([x.track_id for x in solve([TrackRequest("b",100,10,0,500),TrackRequest("a",0,10,0,500)]).scheduled],["a","b"])
