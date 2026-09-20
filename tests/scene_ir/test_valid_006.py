import unittest
from bie.scene_ir.accessibility_validation import *
class T(unittest.TestCase):
 def test_pass(self):
  d={"elements":[{"element_type":"image","accessibility":{"alt":"cell"}}]}
  self.assertTrue(validate_accessibility(d).passed)
 def test_image(self):self.assertFalse(validate_accessibility({"elements":[{"element_type":"image","accessibility":{}}]}).passed)
 def test_video(self):self.assertFalse(validate_accessibility({"elements":[{"element_type":"video","accessibility":{}}]}).passed)
 def test_motion(self):self.assertFalse(validate_accessibility({"elements":[{"element_type":"simulation","accessibility":{}}]}).passed)
 def test_color(self):self.assertFalse(validate_accessibility({"elements":[{"element_type":"chart","accessibility":{"alt":"chart"}}]}).passed)
 def test_not_accepted(self):self.assertFalse(validate_accessibility({"elements":[]}).accepted)
