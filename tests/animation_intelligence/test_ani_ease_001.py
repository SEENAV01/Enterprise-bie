from hashlib import sha256
from bie.animation_intelligence.easing_contracts import *
def ctx(action="transform",**kw):
 d=dict(intent_id="ease",semantic_action=action,evidence_refs=("e",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),narration_revision=2)
 d.update(kw);return MotionContext(**d)

import unittest
from bie.animation_intelligence.easing_semantics import *
class T(unittest.TestCase):
 def test_transform(self):self.assertEqual(select_easing_semantics(ctx("transform")).easing,"ease_in_out")
 def test_trace_linear(self):self.assertEqual(select_easing_semantics(ctx("trace")).easing,"linear")
 def test_constant_rate(self):self.assertEqual(select_easing_semantics(ctx("camera"),constant_rate_semantics=True).easing,"linear")
 def test_constant_rate_block(self):self.assertEqual(select_easing_semantics(ctx("trace"),constant_rate_semantics=True,requested_easing="ease_in").status,"BLOCKED")
 def test_abrupt(self):self.assertEqual(select_easing_semantics(ctx("transform"),abrupt_state_change=True).easing,"step")
 def test_continuity_block(self):self.assertEqual(select_easing_semantics(ctx("transform"),abrupt_state_change=True,continuity_required=True).status,"BLOCKED")
 def test_unsupported(self):self.assertEqual(select_easing_semantics(ctx("unknown")).status,"UNSUPPORTED")
 def test_not_accepted(self):self.assertFalse(select_easing_semantics(ctx("enter")).accepted)
