import unittest
from bie.scene_ir.accessibility_metadata import *
from bie.scene_ir.compiler_capability_declarations import *
from bie.scene_ir.unsupported_capability_failure import *
from bie.scene_ir.planned_fallback_contract import *
class T(unittest.TestCase):
 def test_chain(self):
  self.assertEqual(validate_accessibility_metadata([AccessibilityMetadata("g",alt_text="Demand",color_independent_encoding=True)],{"g":"graph"}),())
  reg=CapabilityRegistry();reg.register(CompilerCapability("cap:static","1",("graph",),(),("web",)));reg.register(CompilerCapability("cap:animated","1",("graph",),("transform",),("video",)))
  self.assertFalse(evaluate_capabilities([CapabilityRequest("cap:animated","g","graph","transform","web","profile_gap")],reg).passed)
  fb=PlannedFallback("fb","g","cap:animated","cap:static","static_graph","degraded_but_safe",True,True,True)
  self.assertEqual(apply_fallback_or_fail(fb,reg,"web","graph")["fallback_action"],"static_graph")
 def test_access_loss_blocks(self):
  reg=CapabilityRegistry();reg.register(CompilerCapability("cap:static","1",("image",),(),("web",)))
  fb=PlannedFallback("fb","i","cap:a","cap:static","static_image","degraded_but_safe",True,True,False)
  with self.assertRaises(SceneIRCapabilityError):apply_fallback_or_fail(fb,reg,"web","image")
