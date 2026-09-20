import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.compiler_capability_declarations import CapabilityRegistry,CompilerCapability
from bie.scene_ir.compiler_capability_resolution import *
class T(unittest.TestCase):
 def reg(self):
  r=CapabilityRegistry();r.register(CompilerCapability("cap:text","1",("text",),("reveal",),("web",)));r.register(CompilerCapability("cap:static","1",("text",),(),("web",)));return r
 def doc(self,fb=True):
  e=UnifiedElement("e","text",{"text":"x"},("s",),("r",));req=({"capability_id":"cap:text","element_id":"e","element_type":"text","requested_action":"reveal","required":True},{"capability_id":"cap:anim","element_id":"e","element_type":"text","requested_action":"morph","required":True});fallback=({"fallback_id":"fb","element_id":"e","missing_capability_id":"cap:anim","fallback_capability_id":"cap:static","fallback_action":"static_focus","semantic_equivalence":"degraded_but_safe","preserves_source_refs":True,"preserves_reasoning_refs":True,"preserves_accessibility":True},) if fb else ()
  return UnifiedSceneIRDocument("s","1.0.0","T",10,(e,),(),("s",),("r",),capability_requests=req,planned_fallbacks=fallback)
 def test_pass(self):self.assertTrue(resolve_compiler_capabilities(self.doc(),self.reg(),"web").passed)
 def test_fallback(self):self.assertEqual(resolve_compiler_capabilities(self.doc(),self.reg(),"web").fallback_ids,("fb",))
 def test_no_fallback(self):self.assertFalse(resolve_compiler_capabilities(self.doc(False),self.reg(),"web").passed)
 def test_profile(self):self.assertFalse(resolve_compiler_capabilities(self.doc(),self.reg(),"video").passed)
 def test_not_accepted(self):self.assertFalse(resolve_compiler_capabilities(self.doc(),self.reg(),"web").accepted)
