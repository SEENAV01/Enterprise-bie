import unittest
from bie.compiler.map_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"m","element_type":"map","props":{"crs":"EPSG:4326","layers":[{"kind":"route","points":[[.1,.2],[.9,.8]]}]},"accessibility":{"alt":"route"},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_svg(self):self.assertIn("<svg",compile_map_element(self.e()).source_text)
 def test_route(self):self.assertIn("const routes",compile_map_element(self.e()).source_text)
 def test_crs(self):self.assertIn("EPSG:4326",compile_map_element(self.e()).source_text)
 def test_layers(self):
  x=self.e();x["props"]["layers"]=[]
  with self.assertRaises(ElementCompilerError):compile_map_element(x)
 def test_no_provider_dependency(self):self.assertEqual(compile_map_element(self.e()).required_dependencies,())
