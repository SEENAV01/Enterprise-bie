import unittest,hashlib
from bie.visual_intelligence.capability_handoff import *
H=hashlib.sha256(b"x").hexdigest()
def p(**kw):
 d=dict(primitive_id="v",primitive_type="vector",required=True,capability_tags=("2d",),fallback_type=None,source_refs=("e",),reasoning_refs=("r",));d.update(kw);return PrimitiveRequirement(**d)
class T(unittest.TestCase):
 def test_pass(self):
  h=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p()],assets=[],timing=[],accessibility_ready=True,target_capabilities={"2d"},target_profile="web");self.assertTrue(assert_handoff_consumable(h))
 def test_unsupported(self):
  h=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p(capability_tags=("3d",))],assets=[],timing=[],accessibility_ready=True,target_capabilities={"2d"},target_profile="web");self.assertTrue(h.unsupported_capabilities)
 def test_fallback(self):
  h=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p(capability_tags=("3d",),fallback_type="diagram")],assets=[],timing=[],accessibility_ready=True,target_capabilities={"2d"},target_profile="web");self.assertEqual(h.planned_fallbacks["v"],"diagram")
 def test_access(self):
  h=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p()],assets=[],timing=[],accessibility_ready=False,target_capabilities={"2d"},target_profile="web");self.assertIn("accessibility:not_ready",h.unsupported_capabilities)
 def test_asset(self):
  a=AssetBinding("a","file://a",H,"source-permitted",("e",));h=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p()],assets=[a],timing=[],accessibility_ready=True,target_capabilities={"2d"},target_profile="web");self.assertEqual(h.assets[0].asset_id,"a")
 def test_bad_asset(self):
  with self.assertRaises(CapabilityHandoffError):build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p()],assets=[AssetBinding("a","",H,"unknown",("e",))],timing=[],accessibility_ready=True,target_capabilities={"2d"},target_profile="web")
 def test_timing(self):
  t=TimingBinding("v",0,100,True,True,2);h=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p()],assets=[],timing=[t],accessibility_ready=True,target_capabilities={"2d"},target_profile="web");self.assertEqual(h.timing[0].narration_revision,2)
 def test_not_accepted(self):
  h=build_downstream_handoff(handoff_id="h",plan_fingerprint=H,primitives=[p()],assets=[],timing=[],accessibility_ready=True,target_capabilities={"2d"},target_profile="web");self.assertFalse(h.accepted)
