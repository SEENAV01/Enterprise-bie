import unittest
from bie.scene_ir.compiler_capability_declarations import *
from bie.scene_ir.unsupported_capability_failure import *
class T(unittest.TestCase):
 def reg(self):
  r=CapabilityRegistry();r.register(CompilerCapability("cap:basic","1",("text",),("reveal",),("web",)));return r
 def test_pass(self):self.assertTrue(evaluate_capabilities([CapabilityRequest("cap:basic","e","text","reveal","web","x")],self.reg()).passed)
 def test_block(self):self.assertFalse(evaluate_capabilities([CapabilityRequest("cap:x","e","text","morph","web","x")],self.reg()).passed)
 def test_optional(self):self.assertTrue(evaluate_capabilities([CapabilityRequest("cap:x","e","text","morph","web","x",False)],self.reg()).passed)
 def test_require(self):
  with self.assertRaises(SceneIRCapabilityError):require_no_required_unsupported(evaluate_capabilities([CapabilityRequest("cap:x","e","text","morph","web","x")],self.reg()))
 def test_not_accepted(self):self.assertFalse(evaluate_capabilities([CapabilityRequest("cap:basic","e","text","reveal","web","x")],self.reg()).accepted)
