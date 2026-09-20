from hashlib import sha256
from bie.animation_intelligence.easing_contracts import *
def ctx(action="transform",**kw):
 d=dict(intent_id="ease",semantic_action=action,evidence_refs=("e",),reasoning_refs=("r",),
        visual_plan_fingerprint=sha256(b"vis").hexdigest(),narration_revision=2)
 d.update(kw);return MotionContext(**d)

import unittest
from bie.animation_intelligence.spring_rules import *
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(configure_spring(ctx("emphasize"),overshoot_allowed=True).status,"PASS")
 def test_parameters(self):self.assertGreater(configure_spring(ctx("emphasize"),overshoot_allowed=True).parameters["natural_frequency"],0)
 def test_physical_block(self):self.assertEqual(configure_spring(ctx("transform"),represents_physical_motion=True,physical_model_verified=False).status,"BLOCKED")
 def test_physical_verified(self):self.assertNotEqual(configure_spring(ctx("transform"),represents_physical_motion=True,physical_model_verified=True,overshoot_allowed=True).status,"BLOCKED")
 def test_rate_sensitive_review(self):self.assertEqual(configure_spring(ctx("trace"),overshoot_allowed=True).status,"REVIEW")
 def test_bad_mass(self):
  with self.assertRaises(SpringRuleError):configure_spring(ctx("emphasize"),mass=0)
 def test_duration(self):self.assertGreater(configure_spring(ctx("emphasize"),overshoot_allowed=True).duration_ms,0)
 def test_not_accepted(self):self.assertFalse(configure_spring(ctx("emphasize"),overshoot_allowed=True).accepted)
