import unittest
from bie.compiler.simulation_compiler import *
class T(unittest.TestCase):
 def e(self,verified=False):return {"element_id":"s","element_type":"simulation","props":{"model_ref":"model:1","initial_state":{"x":1},"execution_class":"verified_observed_execution" if verified else "conceptual",**({"receipt_ref":"rec:1"} if verified else {})},"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_model(self):self.assertIn("data-model-ref",compile_simulation_element(self.e()).source_text)
 def test_state(self):self.assertIn("initialState",compile_simulation_element(self.e()).source_text)
 def test_verified(self):self.assertIn("verified_observed_execution",compile_simulation_element(self.e(True)).source_text)
 def test_receipt(self):
  x=self.e(True);x["props"].pop("receipt_ref")
  with self.assertRaises(ElementCompilerError):compile_simulation_element(x)
 def test_hash(self):self.assertEqual(len(compile_simulation_element(self.e()).source_sha256),64)
