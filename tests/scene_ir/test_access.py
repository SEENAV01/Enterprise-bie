import unittest
from bie.scene_ir.accessibility_metadata import *
class T(unittest.TestCase):
 def test_img(self):self.assertEqual(validate_accessibility_metadata([AccessibilityMetadata("i",alt_text="cell")],{"i":"image"}),())
 def test_img_block(self):self.assertIn("visual_description_missing:i",validate_accessibility_metadata([AccessibilityMetadata("i")],{"i":"image"}))
 def test_video(self):self.assertIn("video_text_alternative_missing:v",validate_accessibility_metadata([AccessibilityMetadata("v")],{"v":"video"}))
 def test_motion(self):self.assertIn("reduced_motion_variant_missing:s",validate_accessibility_metadata([AccessibilityMetadata("s")],{"s":"simulation"}))
 def test_color(self):self.assertIn("color_independent_encoding_missing:c",validate_accessibility_metadata([AccessibilityMetadata("c",alt_text="chart")],{"c":"chart"}))
 def test_color_pass(self):self.assertEqual(validate_accessibility_metadata([AccessibilityMetadata("c",alt_text="chart",color_independent_encoding=True)],{"c":"chart"}),())
 def test_unknown(self):self.assertIn("unknown_element:x",validate_accessibility_metadata([AccessibilityMetadata("x",alt_text="x")],{}))
 def test_dup(self):
  with self.assertRaises(SceneIRCapabilityError):validate_accessibility_metadata([AccessibilityMetadata("x"),AccessibilityMetadata("x")],{"x":"text"})
