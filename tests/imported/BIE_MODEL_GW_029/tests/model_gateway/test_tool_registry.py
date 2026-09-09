
import unittest
from model_gateway.tool_registry import *
class T(unittest.TestCase):
 def d(self):return ToolDescriptor("calc","1",frozenset({"math"}))
 def test_register(self):r=ToolRegistry();r.register(self.d(),1);self.assertEqual(r.resolve("calc","1",{"math"})[1],1)
 def test_deny(self):
  r=ToolRegistry();r.register(self.d(),1)
  with self.assertRaises(ToolRegistryError):r.resolve("calc","1",set())
 def test_duplicate(self):
  r=ToolRegistry();r.register(self.d(),1)
  with self.assertRaises(ToolRegistryError):r.register(self.d(),2)
 def test_missing(self):
  with self.assertRaises(ToolRegistryError):ToolRegistry().resolve("x","1",set())
 def test_sideeffect(self):self.assertFalse(self.d().side_effecting)
if __name__=="__main__":unittest.main()
