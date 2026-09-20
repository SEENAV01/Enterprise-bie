import unittest
from bie.compiler.scene_component_emitter import *
class T(unittest.TestCase):
 def layers(self):return ({"layer_id":"b","component_name":"TextElement","import_path":"./elements/Text","from_frame":30,"duration_in_frames":30,"props":{"text":"B"}},{"layer_id":"a","component_name":"TextElement","import_path":"./elements/Text","from_frame":0,"duration_in_frames":30,"props":{"text":"A"}})
 def test_sequence(self):self.assertIn("<Sequence",emit_scene_component(layers=self.layers()).content)
 def test_order(self):
  c=emit_scene_component(layers=self.layers()).content;self.assertLess(c.index('name={"a"}'),c.index('name={"b"}'))
 def test_absolute_fill(self):self.assertIn("<AbsoluteFill",emit_scene_component(layers=self.layers()).content)
 def test_no_css_animation(self):self.assertNotIn("transition:",emit_scene_component(layers=self.layers()).content)
 def test_bad_duration(self):
  l=list(self.layers());l[0]=dict(l[0]);l[0]["duration_in_frames"]=0
  with self.assertRaises(ReactEmitterError):emit_scene_component(layers=l)
 def test_hash(self):self.assertEqual(len(emit_scene_component(layers=self.layers()).sha256),64)
