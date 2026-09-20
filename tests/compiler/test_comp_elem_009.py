import unittest
from bie.compiler.simulation_compiler import *
from tests.compiler.h2_test_support import sim_props
class T(unittest.TestCase):
 def e(self,verified=False):
  props=sim_props()
  if verified:props.update(execution_class="verified_observed_execution",receipt_ref="rec:1")
  return {"element_id":"s","element_type":"simulation","props":props,"accessibility":{},"source_refs":["s"],"reasoning_refs":["r"]}
 def test_model(self):self.assertIn("data-model-ref",compile_simulation_element(self.e()).source_text)
 def test_state(self):self.assertIn("initialState",compile_simulation_element(self.e()).source_text)
 def test_unverified_receipt_cannot_claim_observed_execution(self):
  with self.assertRaises(ElementCompilerError):compile_simulation_element(self.e(True))
 def test_receipt(self):
  x=self.e(True);x["props"].pop("receipt_ref")
  with self.assertRaises(ElementCompilerError):compile_simulation_element(x)
 def test_hash(self):self.assertEqual(len(compile_simulation_element(self.e()).source_sha256),64)
