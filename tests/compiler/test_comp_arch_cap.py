import unittest
from bie.compiler.compiler_capability_registry import *
class T(unittest.TestCase):
 def c(self,p=10,aid="a"):return CompilerAdapterCapability("cap:text",aid,"1",("text",),("reveal",),("web",),p,True)
 def test_register(self):r=CompilerCapabilityRegistry();self.assertTrue(r.register(self.c()))
 def test_resolve(self):r=CompilerCapabilityRegistry();r.register(self.c());self.assertEqual(r.resolve(element_type="text",action="reveal",profile="web").adapter_id,"a")
 def test_priority(self):
  r=CompilerCapabilityRegistry();r.register(self.c(20,"slow"));r.register(self.c(5,"fast"));self.assertEqual(r.require(element_type="text",action="reveal",profile="web").adapter_id,"fast")
 def test_missing(self):r=CompilerCapabilityRegistry();self.assertIsNone(r.resolve(element_type="map",action="reveal",profile="web"))
 def test_require(self):
  r=CompilerCapabilityRegistry()
  with self.assertRaises(CompilerCapabilityRegistryError):r.require(element_type="text",action="reveal",profile="web")
 def test_duplicate(self):
  r=CompilerCapabilityRegistry();r.register(self.c())
  with self.assertRaises(CompilerCapabilityRegistryError):r.register(self.c())
