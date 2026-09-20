import unittest
from bie.compiler.graph_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"g","element_type":"graph","props":{"series":[{"points":[[0,0],[1,1]]}]},"accessibility":{"alt":"graph"},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_svg(self):self.assertIn("<svg",compile_graph_element(self.e()).source_text)
 def test_path(self):self.assertIn("<path",compile_graph_element(self.e()).source_text)
 def test_series(self):self.assertIn("const series",compile_graph_element(self.e()).source_text)
 def test_short(self):
  x=self.e();x["props"]["series"]=[{"points":[[0,0]]}]
  with self.assertRaises(ElementCompilerError):compile_graph_element(x)
 def test_alt(self):self.assertIn("graph",compile_graph_element(self.e()).source_text)
