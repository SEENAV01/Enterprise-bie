import unittest
from bie.compiler.equation_morph_compiler import *
class T(unittest.TestCase):
 def t(self):return {"track_id":"eqm","element_id":"eq","action":"morph","start_ms":0,"end_ms":1000,"parameters":{"states":["x+x","2x"]},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_states(self):self.assertIn("const states",compile_equation_morph(self.t()).source_text)
 def test_crossfade(self):self.assertIn("opacity: 1 - local",compile_equation_morph(self.t()).source_text)
 def test_warning(self):self.assertTrue(compile_equation_morph(self.t()).warnings)
 def test_short(self):
  x=self.t();x["parameters"]["states"]=["x"]
  with self.assertRaises(AnimationCompilerError):compile_equation_morph(x)
 def test_action(self):
  x=self.t();x["action"]="transform"
  with self.assertRaises(AnimationCompilerError):compile_equation_morph(x)
 def test_not_accepted(self):self.assertFalse(compile_equation_morph(self.t()).accepted)
