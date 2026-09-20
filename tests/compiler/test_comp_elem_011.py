import unittest
from bie.compiler.model3d_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"m3","element_type":"model3d","props":{"resolved_asset_path":"models/cell.glb"},"accessibility":{"alt":"3D cell"},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_canvas(self):self.assertIn("<Canvas",compile_model3d_element(self.e()).source_text)
 def test_gltf(self):self.assertIn("useGLTF",compile_model3d_element(self.e()).source_text)
 def test_dependencies(self):self.assertEqual(set(compile_model3d_element(self.e()).required_dependencies),{"@react-three/fiber","@react-three/drei","three"})
 def test_asset(self):self.assertEqual(compile_model3d_element(self.e()).asset_paths,("models/cell.glb",))
 def test_unresolved(self):
  x=self.e();x["props"]={"asset_ref":"asset://m"}
  with self.assertRaises(ElementCompilerError):compile_model3d_element(x)
