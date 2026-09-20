import unittest
from bie.animation_intelligence.animation_performance_budget import *
def C(**kw):
 d=dict(required_track_ids=("t",),track_count=3,max_simultaneous_tracks=1,particle_count=0,three_d_objects=0,simulation_steps=0,camera_moves=0,asset_bytes=1000);d.update(kw);return AnimationComplexity(**d)
def B():return AnimationBudget("web",20,35,1000,2,5_000_000)
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(evaluate_budget(C(),B()).action,"PASS")
 def test_particles(self):self.assertEqual(evaluate_budget(C(particle_count=2000),B()).action,"SIMPLIFY")
 def test_3d(self):self.assertEqual(evaluate_budget(C(three_d_objects=10),B()).action,"SPLIT_SCENE")
 def test_asset(self):self.assertEqual(evaluate_budget(C(asset_bytes=10_000_000),B()).action,"SIMPLIFY")
 def test_preserve(self):self.assertTrue(assert_required_tracks_preserved(evaluate_budget(C(),B()),["t","x"]))
 def test_loss(self):
  with self.assertRaises(AniPerformanceError):assert_required_tracks_preserved(evaluate_budget(C(),B()),["x"])
 def test_negative(self):
  with self.assertRaises(AniPerformanceError):score_complexity(C(track_count=-1))
 def test_not_accepted(self):self.assertFalse(evaluate_budget(C(),B()).accepted)
