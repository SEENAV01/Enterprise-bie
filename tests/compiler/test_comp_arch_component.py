import unittest
from bie.compiler.component_registry import *
class T(unittest.TestCase):
 def s(self,p=10,cid="text"):return ComponentSpec(cid,"text","TextElement","@bie/primitives/text","cap:text",("web",),("text","role"),p)
 def test_register(self):r=ComponentRegistry();self.assertTrue(r.register(self.s()))
 def test_resolve(self):r=ComponentRegistry();r.register(self.s());self.assertEqual(r.require("text","web").component_name,"TextElement")
 def test_priority(self):
  r=ComponentRegistry();r.register(self.s(20,"b"));r.register(self.s(5,"a"));self.assertEqual(r.resolve("text","web").component_id,"a")
 def test_bad_name(self):
  with self.assertRaises(ComponentRegistryError):ComponentSpec("x","text","bad-name","pkg","cap",("web",))
 def test_bad_import(self):
  with self.assertRaises(ComponentRegistryError):ComponentSpec("x","text","Text","https://x","cap",("web",))
 def test_missing(self):
  r=ComponentRegistry()
  with self.assertRaises(ComponentRegistryError):r.require("map","web")
