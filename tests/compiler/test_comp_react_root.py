import unittest
from bie.compiler.root_emitter import *
class T(unittest.TestCase):
 def test_emit(self):
  f=emit_root();self.assertEqual(f.path,"src/Root.tsx");self.assertIn("export const RemotionRoot",f.content)
 def test_import(self):self.assertIn('from "./Composition"',emit_root().content)
 def test_component(self):self.assertIn("<BieComposition />",emit_root().content)
 def test_bad_name(self):
  with self.assertRaises(ReactEmitterError):emit_root(root_component="bad-name")
 def test_custom(self):self.assertIn("RootX",emit_root(root_component="RootX").content)
 def test_hash(self):self.assertEqual(len(emit_root().sha256),64)
