from hashlib import sha256
from bie.animation_intelligence.easing_contracts import *
def ctx(action="transform",**kw):
 d=dict(intent_id="ease",semantic_action=action,evidence_refs=("e",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),narration_revision=2)
 d.update(kw);return MotionContext(**d)

import unittest
from bie.animation_intelligence.easing_semantics import select_easing_semantics
from bie.animation_intelligence.duration_rules import resolve_duration
from bie.animation_intelligence.spring_rules import configure_spring
from bie.animation_intelligence.motion_reduction import apply_motion_reduction
class T(unittest.TestCase):
 def test_semantic_easing_duration(self):
  e=select_easing_semantics(ctx("transform"))
  d=resolve_duration(ctx("transform"),narration_window_ms=3000)
  self.assertEqual((e.easing,d.status),("ease_in_out","PASS"))
 def test_rate_semantics_guard(self):
  e=select_easing_semantics(ctx("trace"),constant_rate_semantics=True,requested_easing="spring")
  self.assertEqual(e.status,"BLOCKED")
 def test_spring_truth_boundary(self):
  s=configure_spring(ctx("transform"),represents_physical_motion=True,physical_model_verified=False)
  self.assertEqual(s.status,"BLOCKED")
 def test_reduced_motion_pipeline(self):
  r=apply_motion_reduction(ctx("camera",reduced_motion_requested=True),current_easing="ease_in_out",current_duration_ms=900)
  self.assertEqual((r.parameters["replacement_action"],r.easing),("static_focus","step"))
 def test_no_self_acceptance(self):
  self.assertFalse(resolve_duration(ctx("enter"),narration_window_ms=1000).accepted)
