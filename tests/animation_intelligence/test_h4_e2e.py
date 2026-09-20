import unittest,hashlib
from bie.animation_intelligence.ani_actual_e2e import *
H=hashlib.sha256(b"vis").hexdigest()
def V(action="reveal",reduced=None):
 return {"handoff_id":"vh","plan_fingerprint":H,
 "primitives":[{"primitive_id":"v","source_refs":["s"],"reasoning_refs":["r"],"animation_action":action,
                "reduced_motion_variant":reduced}],
 "assets":[],"timing":[{"start_ms":0,"end_ms":100}],"accessibility_ready":True,"target_profile":"web",
 "handoff_fingerprint":hashlib.sha256(b"h").hexdigest(),"current":True,"unsupported_capabilities":[],"planned_fallbacks":{}}
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(run_vis_to_sceneir_ready("r",V(),visual_revision=1,narration_revision=1,target_profile="web").status,"PASS")
 def test_schedule(self):self.assertEqual(run_vis_to_sceneir_ready("r",V(),visual_revision=1,narration_revision=1,target_profile="web").scheduled_track_ids,("v",))
 def test_trace(self):self.assertTrue(run_vis_to_sceneir_ready("r",V(),visual_revision=1,narration_revision=1,target_profile="web").trace_passed)
 def test_reduced_block(self):self.assertEqual(run_vis_to_sceneir_ready("r",V("camera"),visual_revision=1,narration_revision=1,target_profile="web",reduced_motion_requested=True).status,"BLOCKED")
 def test_reduced_pass(self):self.assertEqual(run_vis_to_sceneir_ready("r",V("camera","static_focus"),visual_revision=1,narration_revision=1,target_profile="web",reduced_motion_requested=True).status,"PASS")
 def test_sceneir(self):self.assertTrue(run_vis_to_sceneir_ready("r",V(),visual_revision=1,narration_revision=1,target_profile="web").sceneir_handoff_id.startswith("sceneir:"))
 def test_not_accepted(self):self.assertFalse(run_vis_to_sceneir_ready("r",V(),visual_revision=1,narration_revision=1,target_profile="web").accepted)
