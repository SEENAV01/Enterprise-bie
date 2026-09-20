import unittest
from bie.compiler.particle_compiler import *
class T(unittest.TestCase):
 def e(self):return {"element_id":"p","element_type":"particle_system","props":{"particle_count":20,"physical_claim":True,"receipt_ref":"rec:1"},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_count(self):self.assertIn("const count = 20",compile_particle_element(self.e()).source_text)
 def test_deterministic_positions(self):self.assertIn("(index * 37) % 100",compile_particle_element(self.e()).source_text)
 def test_receipt(self):
  x=self.e();x["props"].pop("receipt_ref")
  with self.assertRaises(ElementCompilerError):compile_particle_element(x)
 def test_limit(self):
  x=self.e();x["props"]["particle_count"]=3000
  with self.assertRaises(ElementCompilerError):compile_particle_element(x)
 def test_hash(self):self.assertEqual(len(compile_particle_element(self.e()).source_sha256),64)
