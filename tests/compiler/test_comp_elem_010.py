import unittest
from bie.compiler.model2d_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"m2","element_type":"model2d","props":{"vertices":[[0,0],[1,1]],"edges":[[0,1]]},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_svg(self):self.assertIn("<svg",compile_model2d_element(self.e()).source_text)
 def test_edges(self):self.assertIn("const edges",compile_model2d_element(self.e()).source_text)
 def test_vertices(self):self.assertIn("const vertices",compile_model2d_element(self.e()).source_text)
 def test_short(self):
  x=self.e();x["props"]["vertices"]=[[0,0]]
  with self.assertRaises(ElementCompilerError):compile_model2d_element(x)
 def test_hash(self):self.assertEqual(len(compile_model2d_element(self.e()).source_sha256),64)
