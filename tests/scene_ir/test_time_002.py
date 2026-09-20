import unittest
from bie.scene_ir.animation_tracks import *
def T(i="t",e="e",s=0,en=100):return AnimationTrackSpec(i,e,"reveal",s,en,"linear",{},("src",),("r",))
class X(unittest.TestCase):
 def test_pass(self):self.assertEqual(validate_tracks([T()],("e",),100),())
 def test_unknown(self):self.assertEqual(validate_tracks([T(e="x")],("e",),100),("unknown_element:t",))
 def test_over(self):self.assertEqual(validate_tracks([T(en=101)],("e",),100),("track_exceeds_scene:t",))
 def test_easing(self):
  with self.assertRaises(TemporalIRError):AnimationTrackSpec("t","e","x",0,10,"bounce",{},("s",),("r",))
 def test_lineage(self):
  with self.assertRaises(TemporalIRError):AnimationTrackSpec("t","e","x",0,10,"linear",{},(),("r",))
