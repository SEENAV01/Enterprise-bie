from hashlib import sha256
from bie.animation_intelligence.easing_contracts import *
def ctx(action="transform",**kw):
 d=dict(intent_id="ease",semantic_action=action,evidence_refs=("e",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),narration_revision=2)
 d.update(kw);return MotionContext(**d)

import unittest
from bie.animation_intelligence.motion_reduction import *
class T(unittest.TestCase):
 def test_no_request(self):self.assertFalse(apply_motion_reduction(ctx("camera"),current_easing="ease_in_out",current_duration_ms=900).parameters["reduced_motion_applied"])
 def test_camera_static(self):self.assertEqual(apply_motion_reduction(ctx("camera",reduced_motion_requested=True),current_easing="ease_in_out",current_duration_ms=900).parameters["replacement_action"],"static_focus")
 def test_path_static(self):self.assertEqual(apply_motion_reduction(ctx("path_follow",reduced_motion_requested=True),current_easing="linear",current_duration_ms=1200).parameters["replacement_action"],"static_path")
 def test_path_essential(self):self.assertEqual(apply_motion_reduction(ctx("path_follow",reduced_motion_requested=True),current_easing="linear",current_duration_ms=1200,essential_semantic_motion=True).status,"REVIEW")
 def test_morph_crossfade(self):self.assertEqual(apply_motion_reduction(ctx("morph",reduced_motion_requested=True),current_easing="ease_in_out",current_duration_ms=900).parameters["replacement_action"],"crossfade_states")
 def test_sim_snapshots(self):self.assertEqual(apply_motion_reduction(ctx("simulation_state",reduced_motion_requested=True),current_easing="linear",current_duration_ms=800).parameters["replacement_action"],"state_snapshots")
 def test_bad_duration(self):
  with self.assertRaises(DurationError):apply_motion_reduction(ctx("camera"),current_easing="linear",current_duration_ms=0)
 def test_not_accepted(self):self.assertFalse(apply_motion_reduction(ctx("camera",reduced_motion_requested=True),current_easing="linear",current_duration_ms=900).accepted)
