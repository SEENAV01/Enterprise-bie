import unittest
from bie.compiler.camera_compiler import *
class T(unittest.TestCase):
 def t(self):return {"track_id":"cam","element_id":"scene","action":"camera","start_ms":0,"end_ms":1000,"parameters":{"from":{"x":0,"y":0,"scale":1,"rotation_deg":0},"to":{"x":20,"y":10,"scale":1.5,"rotation_deg":5}},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_translate(self):self.assertIn("translate: interpolate",compile_camera_track(self.t()).source_text)
 def test_scale(self):self.assertIn('output: "perceptual-scale"',compile_camera_track(self.t()).source_text)
 def test_rotate(self):self.assertIn("rotate: interpolate",compile_camera_track(self.t()).source_text)
 def test_no_transform_string(self):self.assertNotIn("transform:",compile_camera_track(self.t()).source_text)
 def test_bad_scale(self):
  x=self.t();x["parameters"]["to"]["scale"]=0
  with self.assertRaises(AnimationCompilerError):compile_camera_track(x)
 def test_type(self):
  x=self.t();x["action"]="reveal"
  with self.assertRaises(AnimationCompilerError):compile_camera_track(x)
