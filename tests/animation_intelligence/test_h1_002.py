import unittest,hashlib
from bie.animation_intelligence.vis_ani_adoption import *
H=hashlib.sha256(b"v").hexdigest()
def R(**kw):
 d={"handoff_id":"vh","plan_fingerprint":H,"primitives":[{"primitive_id":"v","source_refs":["s"],"reasoning_refs":["r"]}],"timing":[{"start_ms":0,"end_ms":100}],"accessibility_ready":True,"target_profile":"web","current":True,"unsupported_capabilities":[],"planned_fallbacks":{}};d.update(kw);return d
class T(unittest.TestCase):
 def test_pass(self):self.assertEqual(adopt_visual_handoff(R(),1).handoff_id,"vh")
 def test_stale(self):
  with self.assertRaises(StaleVisualHandoffError):adopt_visual_handoff(R(current=False),1)
 def test_access(self):
  with self.assertRaises(VisAdoptionError):adopt_visual_handoff(R(accessibility_ready=False),1)
 def test_unresolved(self):
  with self.assertRaises(VisAdoptionError):adopt_visual_handoff(R(unsupported_capabilities=["v:3d"]),1)
 def test_fallback(self):self.assertFalse(adopt_visual_handoff(R(unsupported_capabilities=["v:3d"],planned_fallbacks={"v":"2d"}),1).accepted)
