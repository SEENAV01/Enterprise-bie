import unittest
from bie.compiler.equation_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"eq","element_type":"equation","props":{"expression":"F=ma","format":"latex","side_conditions":["m>0"]},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_type(self):self.assertEqual(compile_equation_element(self.e()).element_type,"equation")
 def test_math_role(self):self.assertIn('role="math"',compile_equation_element(self.e()).source_text)
 def test_side(self):self.assertIn("sideConditions",compile_equation_element(self.e()).source_text)
 def test_warning(self):self.assertTrue(compile_equation_element(self.e()).warnings)
 def test_bad_format(self):
  x=self.e();x["props"]["format"]="svg"
  with self.assertRaises(ElementCompilerError):compile_equation_element(x)
