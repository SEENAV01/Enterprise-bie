import unittest
from bie.compiler.vector_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"v","element_type":"vector","props":{"components":[3,4],"label":"F"},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_svg(self):self.assertIn("<svg",compile_vector_element(self.e()).source_text)
 def test_arrow(self):self.assertIn("markerEnd",compile_vector_element(self.e()).source_text)
 def test_hash(self):self.assertEqual(len(compile_vector_element(self.e()).source_sha256),64)
 def test_bad_dim(self):
  x=self.e();x["props"]["components"]=[1]
  with self.assertRaises(ElementCompilerError):compile_vector_element(x)
 def test_not_accepted(self):self.assertFalse(compile_vector_element(self.e()).accepted)
