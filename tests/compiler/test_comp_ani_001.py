import unittest
from bie.compiler.animation_track_compiler import *
class T(unittest.TestCase):
 def t(self):return {"track_id":"t","element_id":"e","action":"reveal","start_ms":0,"end_ms":1000,"parameters":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_frame(self):self.assertIn("useCurrentFrame()",compile_animation_track(self.t()).source_text)
 def test_interpolate(self):self.assertIn("interpolate(",compile_animation_track(self.t()).source_text)
 def test_clamp(self):self.assertIn('extrapolateRight: "clamp"',compile_animation_track(self.t()).source_text)
 def test_action(self):self.assertIn('data-bie-action={"reveal"}',compile_animation_track(self.t()).source_text)
 def test_bad_action(self):
  x=self.t();x["action"]="explode"
  with self.assertRaises(AnimationCompilerError):compile_animation_track(x)
 def test_not_accepted(self):self.assertFalse(compile_animation_track(self.t()).accepted)
