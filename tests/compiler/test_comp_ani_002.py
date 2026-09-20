import unittest
from bie.compiler.semantic_easing_compiler import *
class T(unittest.TestCase):
 def test_gentle(self):self.assertIn("Easing.bezier",easing_expression("gentle"))
 def test_linear(self):self.assertEqual(easing_expression("linear"),"Easing.linear")
 def test_module(self):self.assertIn("semanticEasing",compile_semantic_easing_module(["gentle","linear"]).source_text)
 def test_deterministic(self):self.assertEqual(compile_semantic_easing_module(["linear","gentle"]).source_sha256,compile_semantic_easing_module(["gentle","linear"]).source_sha256)
 def test_bad(self):
  with self.assertRaises(AnimationCompilerError):easing_expression("random")
 def test_empty(self):
  with self.assertRaises(AnimationCompilerError):compile_semantic_easing_module([])
