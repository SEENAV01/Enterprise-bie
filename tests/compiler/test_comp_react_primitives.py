import unittest
from bie.compiler.reusable_primitives_emitter import *
class T(unittest.TestCase):
 def content(self):return emit_reusable_primitives().content
 def test_frame_driven(self):self.assertIn("useCurrentFrame()",self.content())
 def test_interpolate(self):self.assertIn("interpolate(",self.content())
 def test_easing(self):self.assertIn("Easing.bezier",self.content())
 def test_clamp(self):self.assertIn('extrapolateLeft: "clamp"',self.content())
 def test_no_css_transition(self):self.assertNotIn("transition:",self.content())
 def test_no_css_animation(self):self.assertNotIn("animation:",self.content())
 def test_hash(self):self.assertEqual(len(emit_reusable_primitives().sha256),64)
