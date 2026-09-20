import unittest
from bie.animation_intelligence.ani_accessibility import *
class X:
 def __init__(self,i,a,reduced=None,p=None):self.track_id=i;self.semantic_action=a;self.reduced_motion_variant=reduced;self.payload=p or {}
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(enforce_animation_accessibility([X("t","reveal")],AccessibilityPolicy(False)).status,"PASS")
 def test_missing_variant(self):self.assertEqual(enforce_animation_accessibility([X("t","camera")],AccessibilityPolicy(True)).status,"BLOCKED")
 def test_variant(self):self.assertEqual(enforce_animation_accessibility([X("t","camera","static_focus")],AccessibilityPolicy(True)).status,"PASS")
 def test_flash(self):self.assertEqual(enforce_animation_accessibility([X("t","reveal",p={"flash_hz":4})],AccessibilityPolicy(False)).status,"BLOCKED")
 def test_orbit(self):self.assertEqual(enforce_animation_accessibility([X("t","camera",p={"camera_mode":"orbit"})],AccessibilityPolicy(False,allow_orbit_camera=False)).status,"BLOCKED")
 def test_replacement(self):self.assertIn(("t","static_trace"),enforce_animation_accessibility([X("t","trace","static_trace")],AccessibilityPolicy(True)).replacements)
 def test_require(self):
  with self.assertRaises(AniAccessibilityError):require_accessibility_pass(enforce_animation_accessibility([X("t","camera")],AccessibilityPolicy(True)))
 def test_not_accepted(self):self.assertFalse(enforce_animation_accessibility([X("t","reveal")],AccessibilityPolicy(False)).accepted)
