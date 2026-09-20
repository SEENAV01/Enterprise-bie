from hashlib import sha256
from bie.animation_intelligence.easing_contracts import *
def ctx(action="transform",**kw):
 d=dict(intent_id="ease",semantic_action=action,evidence_refs=("e",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),narration_revision=2)
 d.update(kw);return MotionContext(**d)

import unittest
from bie.animation_intelligence.duration_rules import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(resolve_duration(ctx("enter"),narration_window_ms=1000).status,"PASS")
 def test_complexity_increases(self):self.assertGreater(resolve_duration(ctx("transform",complexity=1),narration_window_ms=5000).duration_ms,resolve_duration(ctx("transform",complexity=0),narration_window_ms=5000).duration_ms)
 def test_steps_increase(self):self.assertGreater(resolve_duration(ctx("reveal"),narration_window_ms=5000,semantic_steps=4).duration_ms,resolve_duration(ctx("reveal"),narration_window_ms=5000,semantic_steps=1).duration_ms)
 def test_extension_review(self):self.assertEqual(resolve_duration(ctx("morph",complexity=1),narration_window_ms=200,allow_scene_extension=True).status,"REVIEW")
 def test_short_block(self):self.assertEqual(resolve_duration(ctx("morph",complexity=1),narration_window_ms=200,allow_scene_extension=False).status,"BLOCKED")
 def test_bad_window(self):
  with self.assertRaises(DurationError):resolve_duration(ctx("enter"),narration_window_ms=0)
 def test_bounds(self):self.assertLessEqual(resolve_duration(ctx("path_follow"),narration_window_ms=5000,max_ms=700).duration_ms,700)
 def test_not_accepted(self):self.assertFalse(resolve_duration(ctx("enter"),narration_window_ms=1000).accepted)
