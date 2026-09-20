import unittest
from bie.scene_ir.compiler_capability_declarations import *
class T(unittest.TestCase):
 def c(self):return CompilerCapability("cap:text","1",("text",),("reveal","enter"),("web","video"))
 def test_reg(self):r=CapabilityRegistry();self.assertTrue(r.register(self.c()))
 def test_support(self):r=CapabilityRegistry();r.register(self.c());self.assertTrue(r.supports("cap:text","text","reveal","web"))
 def test_elem(self):r=CapabilityRegistry();r.register(self.c());self.assertFalse(r.supports("cap:text","graph","reveal","web"))
 def test_action(self):r=CapabilityRegistry();r.register(self.c());self.assertFalse(r.supports("cap:text","text","morph","web"))
 def test_profile(self):r=CapabilityRegistry();r.register(self.c());self.assertFalse(r.supports("cap:text","text","reveal","vr"))
 def test_dup(self):
  r=CapabilityRegistry();r.register(self.c())
  with self.assertRaises(SceneIRCapabilityError):r.register(self.c())
 def test_snapshot(self):r=CapabilityRegistry();r.register(self.c());self.assertEqual(len(r.snapshot()),1)
